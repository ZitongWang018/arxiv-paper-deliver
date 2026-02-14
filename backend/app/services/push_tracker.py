"""In-memory push task status tracker.

Tracks the progress of push tasks so the frontend can poll for updates.
Tasks are short-lived (minutes) and auto-expire after 1 hour.
"""

import time
import uuid
from enum import Enum
from threading import Lock
from typing import Optional


class PushStep(str, Enum):
    QUEUED = "queued"
    FETCHING_PAPERS = "fetching_papers"
    ANALYZING = "analyzing"
    SENDING_EMAIL = "sending_email"
    COMPLETED = "completed"
    FAILED = "failed"


STEP_LABELS: dict[PushStep, str] = {
    PushStep.QUEUED: "排队中...",
    PushStep.FETCHING_PAPERS: "正在从 arXiv 抓取论文...",
    PushStep.ANALYZING: "正在用 LLM 分析论文相关性...",
    PushStep.SENDING_EMAIL: "正在发送推荐邮件...",
    PushStep.COMPLETED: "推送完成！",
    PushStep.FAILED: "推送失败",
}

STEP_PROGRESS: dict[PushStep, int] = {
    PushStep.QUEUED: 0,
    PushStep.FETCHING_PAPERS: 20,
    PushStep.ANALYZING: 50,
    PushStep.SENDING_EMAIL: 80,
    PushStep.COMPLETED: 100,
    PushStep.FAILED: 100,
}


class PushTask:
    """Represents the status of one push operation."""

    def __init__(self, task_id: str, subscription_id: int):
        self.task_id = task_id
        self.subscription_id = subscription_id
        self.step = PushStep.QUEUED
        self.message = STEP_LABELS[PushStep.QUEUED]
        self.progress = 0
        self.papers_found: int = 0
        self.papers_relevant: int = 0
        self.papers_sent: int = 0
        self.error: Optional[str] = None
        self.created_at = time.time()

    def advance(self, step: PushStep, message: Optional[str] = None, **kwargs: object) -> None:
        self.step = step
        self.message = message or STEP_LABELS.get(step, "")
        self.progress = STEP_PROGRESS.get(step, 0)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def fail(self, error_message: str) -> None:
        self.step = PushStep.FAILED
        self.message = f"推送失败：{error_message}"
        self.progress = 100
        self.error = error_message

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "subscription_id": self.subscription_id,
            "step": self.step.value,
            "message": self.message,
            "progress": self.progress,
            "papers_found": self.papers_found,
            "papers_relevant": self.papers_relevant,
            "papers_sent": self.papers_sent,
            "error": self.error,
            "is_done": self.step in (PushStep.COMPLETED, PushStep.FAILED),
        }


# ── Global task store ────────────────────────────────

_tasks: dict[str, PushTask] = {}
_lock = Lock()
_TTL_SECONDS = 3600  # auto-expire after 1 hour


def create_task(subscription_id: int) -> PushTask:
    """Create and register a new push task."""
    _cleanup_expired()
    task_id = uuid.uuid4().hex[:12]
    task = PushTask(task_id=task_id, subscription_id=subscription_id)
    with _lock:
        _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[PushTask]:
    """Get a task by ID."""
    with _lock:
        return _tasks.get(task_id)


def _cleanup_expired() -> None:
    """Remove tasks older than TTL."""
    now = time.time()
    with _lock:
        expired = [tid for tid, t in _tasks.items() if now - t.created_at > _TTL_SECONDS]
        for tid in expired:
            del _tasks[tid]
