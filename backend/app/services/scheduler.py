"""APScheduler-based task scheduler for daily paper digest pushes."""

import logging
from datetime import date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import Subscription, User, PushRecord
from app.auth import create_access_token
from app.config import get_settings
from app.services import arxiv_service, llm_service, email_service
from app.services.push_tracker import PushTask, PushStep, create_task

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


async def _execute_subscription_push(
    subscription_id: int,
    task: PushTask | None = None,
) -> None:
    """Core pipeline: fetch -> analyze -> email for a single subscription."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.id == subscription_id,
                    Subscription.is_active == True,  # noqa: E712
                )
            )
            sub = result.scalar_one_or_none()
            if sub is None:
                msg = f"Subscription {subscription_id} not found or inactive"
                logger.warning("%s, skipping.", msg)
                if task:
                    task.fail("订阅不存在或已暂停")
                return

            # Idempotency guard for daily mode: skip if already pushed today.
            if sub.auto_daily:
                day_start = datetime.combine(date.today(), datetime.min.time())
                day_end = day_start + timedelta(days=1)
                existing = await db.execute(
                    select(PushRecord.id).where(
                        PushRecord.subscription_id == sub.id,
                        PushRecord.pushed_at >= day_start,
                        PushRecord.pushed_at < day_end,
                    ).limit(1)
                )
                if existing.scalar_one_or_none() is not None:
                    logger.info(
                        "Subscription %d already pushed today, skipping duplicate daily run.",
                        sub.id,
                    )
                    if task:
                        task.fail("今日已推送过，请勿重复推送")
                    return

            user_result = await db.execute(select(User).where(User.id == sub.user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                logger.error("User %d not found for subscription %d", sub.user_id, subscription_id)
                if task:
                    task.fail("用户账号异常")
                return

            # 1. Determine date range
            if sub.auto_daily:
                start = date.today()
                end = date.today()
            elif sub.start_date and sub.end_date:
                start = sub.start_date
                end = sub.end_date
            else:
                start = date.today()
                end = date.today()

            # 2. Fetch papers from arxiv
            if task:
                task.advance(
                    PushStep.FETCHING_PAPERS,
                    f"正在从 arXiv 抓取论文（{start} ~ {end}）...",
                )
            logger.info("Fetching papers for subscription '%s' (%s -> %s)", sub.name, start, end)
            raw_papers = await arxiv_service.fetch_papers(
                arxiv_categories=sub.arxiv_categories,
                start_date=start if (sub.start_date or sub.auto_daily) else None,
                end_date=end if (sub.end_date or sub.auto_daily) else None,
                max_results=200,
            )
            if not raw_papers:
                logger.info("No papers found for subscription '%s'", sub.name)
                if task:
                    task.fail("未找到论文，请检查日期范围或 arXiv 分类是否正确")
                return

            if task:
                task.advance(
                    PushStep.ANALYZING,
                    f"已抓取 {len(raw_papers)} 篇论文，正在用 {sub.llm_provider} 分析相关性...",
                    papers_found=len(raw_papers),
                )

            # 3. LLM analysis
            logger.info("Analyzing %d papers with %s", len(raw_papers), sub.llm_provider)
            analyzed = await llm_service.analyze_papers(
                papers=raw_papers,
                research_interest=sub.research_interest,
                provider=sub.llm_provider,
                api_key=sub.llm_api_key,
                model=sub.llm_model,
            )

            # 4. Select top-k relevant papers
            top_papers = [p for p in analyzed if p.get("relevance_score", 0) >= 5][:sub.max_papers]
            if not top_papers:
                logger.info("No relevant papers found for subscription '%s'", sub.name)
                if task:
                    task.fail(
                        f"在 {len(raw_papers)} 篇论文中未找到高相关性结果（评分 >= 5），"
                        "请尝试调整研究兴趣描述或扩大日期范围"
                    )
                return

            if task:
                task.advance(
                    PushStep.SENDING_EMAIL,
                    f"找到 {len(top_papers)} 篇相关论文，正在发送邮件...",
                    papers_relevant=len(top_papers),
                )

            # 5. Upsert papers into DB and create push records
            orm_papers = await arxiv_service.upsert_papers(db, top_papers)
            for orm_paper, analysis_data in zip(orm_papers, top_papers):
                record = PushRecord(
                    subscription_id=sub.id,
                    paper_id=orm_paper.id,
                    relevance_score=analysis_data.get("relevance_score", 0),
                    relevance_reason=analysis_data.get("relevance_reason", ""),
                    abstract_zh=analysis_data.get("abstract_zh", ""),
                )
                db.add(record)

            # 6. Generate JWT token for star links (long-lived)
            token = create_access_token(
                data={"sub": user.id},
                expires_delta=timedelta(days=90),
            )

            # 7. Prepare email data
            email_papers = []
            for orm_paper, analysis_data in zip(orm_papers, top_papers):
                email_papers.append({
                    "paper_db_id": orm_paper.id,
                    "title": orm_paper.title,
                    "authors": orm_paper.authors,
                    "abstract": orm_paper.abstract,
                    "url": orm_paper.url,
                    "pdf_url": orm_paper.pdf_url,
                    "relevance_score": analysis_data.get("relevance_score", 0),
                    "relevance_reason": analysis_data.get("relevance_reason", ""),
                    "abstract_zh": analysis_data.get("abstract_zh", ""),
                })

            html = email_service.render_digest_email(
                papers=email_papers,
                subscription_name=sub.name,
                research_interest=sub.research_interest,
                user_token=token,
                base_url=settings.BASE_URL,
                frontend_url=settings.FRONTEND_URL,
            )

            # 8. Send email
            subject = f"📄 ArxivDigest - {sub.name} ({date.today().isoformat()})"
            email_ok, email_error = await email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_body=html,
            )

            if not email_ok:
                if task:
                    task.fail(f"论文已分析完成，但邮件发送失败：{email_error}")
                logger.error("Email send failed for subscription '%s': %s", sub.name, email_error)
                await db.rollback()
                return

            await db.commit()
            logger.info("Push completed for subscription '%s': %d papers sent to %s",
                        sub.name, len(email_papers), user.email)

            if task:
                task.advance(
                    PushStep.COMPLETED,
                    f"推送完成！已将 {len(email_papers)} 篇论文发送到 {user.email}",
                    papers_sent=len(email_papers),
                )

        except Exception as exc:
            logger.exception("Push failed for subscription %d: %s", subscription_id, exc)
            await db.rollback()
            if task:
                task.fail(f"系统错误：{str(exc)[:200]}")


def _job_id(subscription_id: int) -> str:
    return f"sub_{subscription_id}_daily"


def schedule_subscription(sub_id: int, cron_time: str = "08:00") -> None:
    """Add or update a daily cron job for a subscription."""
    job_id = _job_id(sub_id)
    parts = cron_time.split(":")
    hour = int(parts[0]) if len(parts) > 0 else 8
    minute = int(parts[1]) if len(parts) > 1 else 0

    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.reschedule_job(
            job_id,
            trigger=CronTrigger(hour=hour, minute=minute),
        )
    else:
        scheduler.add_job(
            _execute_subscription_push,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[sub_id],
            id=job_id,
            replace_existing=True,
        )
    logger.info("Scheduled daily push for subscription %d at %02d:%02d", sub_id, hour, minute)


def unschedule_subscription(sub_id: int) -> None:
    """Remove the daily cron job for a subscription."""
    job_id = _job_id(sub_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Unscheduled daily push for subscription %d", sub_id)


async def trigger_push_now(subscription_id: int, task: PushTask | None = None) -> None:
    """Trigger an immediate push for a subscription (manual)."""
    await _execute_subscription_push(subscription_id, task=task)


async def trigger_all_active_auto_daily_pushes() -> int:
    """Trigger pushes for all active auto_daily subscriptions."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Subscription.id).where(
                Subscription.auto_daily == True,  # noqa: E712
                Subscription.is_active == True,  # noqa: E712
            )
        )
        sub_ids = list(result.scalars().all())

    for sub_id in sub_ids:
        await _execute_subscription_push(sub_id)
    logger.info("External cron triggered %d active auto_daily subscriptions", len(sub_ids))
    return len(sub_ids)


async def restore_scheduled_jobs() -> None:
    """On startup, re-schedule all active auto_daily subscriptions."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Subscription).where(
                Subscription.auto_daily == True,  # noqa: E712
                Subscription.is_active == True,  # noqa: E712
            )
        )
        subs = result.scalars().all()
        for sub in subs:
            schedule_subscription(sub.id, sub.cron_time or "08:00")
        logger.info("Restored %d scheduled jobs on startup", len(subs))


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
