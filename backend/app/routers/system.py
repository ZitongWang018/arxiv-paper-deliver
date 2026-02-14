"""System-level endpoints for external cron integrations."""

from fastapi import APIRouter, HTTPException, Query, status

from app.config import get_settings
from app.services.scheduler import trigger_all_active_auto_daily_pushes

router = APIRouter(prefix="/api/system", tags=["system"])
settings = get_settings()


@router.post("/cron/run")
async def run_daily_cron(secret: str = Query(default="")):
    """Trigger daily pushes from an external scheduler (e.g. cron-job.org)."""
    if not settings.CRON_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRON_SECRET_KEY is not configured",
        )
    if secret != settings.CRON_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret")

    count = await trigger_all_active_auto_daily_pushes()
    return {"message": "cron run completed", "triggered_subscriptions": count}
