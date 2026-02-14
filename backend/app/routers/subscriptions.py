"""Subscription CRUD and manual trigger router."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Subscription, PushRecord
from app.schemas import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionOut,
    PushRecordOut, TriggerPushRequest,
)
from app.auth import get_current_user
from app.services.scheduler import schedule_subscription, unschedule_subscription, trigger_push_now
from app.services.push_tracker import create_task, get_task

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = Subscription(
        user_id=current_user.id,
        name=payload.name,
        research_interest=payload.research_interest,
        llm_provider=payload.llm_provider,
        llm_api_key=payload.llm_api_key,
        llm_model=payload.llm_model,
        arxiv_categories=payload.arxiv_categories,
        max_papers=payload.max_papers,
        start_date=payload.start_date,
        end_date=payload.end_date,
        auto_daily=payload.auto_daily,
        cron_time=payload.cron_time or "08:00",
    )
    db.add(sub)
    await db.flush()
    await db.commit()

    if sub.auto_daily:
        schedule_subscription(sub.id, sub.cron_time or "08:00")

    return sub


@router.get("/{sub_id}", response_model=SubscriptionOut)
async def get_subscription(
    sub_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return sub


@router.put("/{sub_id}", response_model=SubscriptionOut)
async def update_subscription(
    sub_id: int,
    payload: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)
    await db.flush()
    await db.commit()

    # Update scheduler
    if sub.auto_daily and sub.is_active:
        schedule_subscription(sub.id, sub.cron_time or "08:00")
    else:
        unschedule_subscription(sub.id)

    return sub


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    sub_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    unschedule_subscription(sub.id)
    await db.delete(sub)
    await db.commit()


@router.post("/{sub_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_push(
    sub_id: int,
    payload: TriggerPushRequest = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a push for a subscription. Returns task_id for polling."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    # Optionally override date range
    if payload and payload.start_date:
        sub.start_date = payload.start_date
    if payload and payload.end_date:
        sub.end_date = payload.end_date
    await db.flush()
    await db.commit()

    task = create_task(subscription_id=sub_id)
    background_tasks.add_task(trigger_push_now, sub_id, task)
    return {"message": "推送任务已提交", "task_id": task.task_id}


@router.get("/{sub_id}/push-status/{task_id}")
async def get_push_status(
    sub_id: int,
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll push task status."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.subscription_id != sub_id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    return task.to_dict()


@router.get("/{sub_id}/history", response_model=list[PushRecordOut])
async def get_push_history(
    sub_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get push history for a subscription."""
    # Verify ownership
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="订阅不存在")

    result = await db.execute(
        select(PushRecord)
        .where(PushRecord.subscription_id == sub_id)
        .options(selectinload(PushRecord.paper))
        .order_by(PushRecord.pushed_at.desc())
        .limit(100)
    )
    return result.scalars().all()
