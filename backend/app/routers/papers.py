"""Paper-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Paper
from app.schemas import PaperOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single paper by ID (public endpoint for star confirmation)."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    return paper


@router.get("", response_model=list[PaperOut])
async def search_papers(
    q: str = Query(default="", description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Search papers by title keyword (simple)."""
    stmt = select(Paper).order_by(Paper.id.desc()).limit(limit)
    if q:
        stmt = select(Paper).where(Paper.title.ilike(f"%{q}%")).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
