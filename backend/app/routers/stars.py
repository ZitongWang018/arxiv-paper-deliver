"""Star (bookmark) management router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Paper, StarredPaper
from app.schemas import StarCreate, StarUpdate, StarredPaperOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/stars", tags=["stars"])


@router.get("", response_model=list[StarredPaperOut])
async def list_starred(
    tag: str = Query(default="", description="Filter by tag"),
    search: str = Query(default="", description="Search in title"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all starred papers for the current user."""
    stmt = (
        select(StarredPaper)
        .where(StarredPaper.user_id == current_user.id)
        .options(selectinload(StarredPaper.paper))
        .order_by(StarredPaper.starred_at.desc())
    )
    result = await db.execute(stmt)
    stars = result.scalars().all()

    # In-memory filtering for simplicity (SQLite JSON support is limited)
    if tag:
        stars = [s for s in stars if tag.lower() in (s.tags or "").lower()]
    if search:
        stars = [s for s in stars if search.lower() in (s.paper.title or "").lower()]

    return stars


@router.post("", response_model=StarredPaperOut, status_code=status.HTTP_201_CREATED)
async def star_paper(
    payload: StarCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Star a paper."""
    # Verify paper exists
    result = await db.execute(select(Paper).where(Paper.id == payload.paper_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="论文不存在")

    # Check if already starred
    result = await db.execute(
        select(StarredPaper).where(
            StarredPaper.user_id == current_user.id,
            StarredPaper.paper_id == payload.paper_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="已收藏该论文")

    star = StarredPaper(
        user_id=current_user.id,
        paper_id=payload.paper_id,
        user_note=payload.user_note or "",
        tags=payload.tags or "",
    )
    db.add(star)
    await db.flush()
    await db.commit()

    # Reload with paper relationship
    result = await db.execute(
        select(StarredPaper)
        .where(StarredPaper.id == star.id)
        .options(selectinload(StarredPaper.paper))
    )
    return result.scalar_one()


@router.put("/{star_id}", response_model=StarredPaperOut)
async def update_star(
    star_id: int,
    payload: StarUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update star notes or tags."""
    result = await db.execute(
        select(StarredPaper)
        .where(StarredPaper.id == star_id, StarredPaper.user_id == current_user.id)
        .options(selectinload(StarredPaper.paper))
    )
    star = result.scalar_one_or_none()
    if not star:
        raise HTTPException(status_code=404, detail="收藏记录不存在")

    if payload.user_note is not None:
        star.user_note = payload.user_note
    if payload.tags is not None:
        star.tags = payload.tags
    await db.flush()
    await db.commit()
    return star


@router.delete("/{star_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unstar_paper(
    star_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a star."""
    result = await db.execute(
        select(StarredPaper).where(
            StarredPaper.id == star_id,
            StarredPaper.user_id == current_user.id,
        )
    )
    star = result.scalar_one_or_none()
    if not star:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    await db.delete(star)
    await db.commit()


@router.get("/tags", response_model=list[str])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all unique tags used by the current user."""
    result = await db.execute(
        select(StarredPaper.tags)
        .where(StarredPaper.user_id == current_user.id)
        .where(StarredPaper.tags != "")
        .where(StarredPaper.tags.isnot(None))
    )
    raw_tags: set[str] = set()
    for (tags_str,) in result.all():
        for t in tags_str.split(","):
            t = t.strip()
            if t:
                raw_tags.add(t)
    return sorted(raw_tags)
