"""SQLAlchemy ORM models."""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date,
    ForeignKey, JSON, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    starred_papers = relationship("StarredPaper", back_populates="user", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    research_interest = Column(Text, nullable=False)
    llm_provider = Column(String(50), nullable=False)  # "qwen" or "deepseek"
    llm_api_key = Column(String(255), nullable=False)
    llm_model = Column(String(100), nullable=True)
    arxiv_categories = Column(JSON, nullable=False)  # e.g. ["cs.AI", "cs.CL"]
    max_papers = Column(Integer, default=5, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    auto_daily = Column(Boolean, default=False, nullable=False)
    cron_time = Column(String(10), default="08:00", nullable=True)  # HH:MM
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="subscriptions")
    push_records = relationship("PushRecord", back_populates="subscription", cascade="all, delete-orphan")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    url = Column(String(500), nullable=False)
    pdf_url = Column(String(500), nullable=False)
    categories = Column(String(500), nullable=True)
    published_date = Column(Date, nullable=True)

    push_records = relationship("PushRecord", back_populates="paper")
    starred_by = relationship("StarredPaper", back_populates="paper")


class PushRecord(Base):
    __tablename__ = "push_records"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    relevance_score = Column(Float, nullable=False)
    relevance_reason = Column(Text, nullable=True)
    abstract_zh = Column(Text, nullable=True)
    pushed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subscription = relationship("Subscription", back_populates="push_records")
    paper = relationship("Paper", back_populates="push_records")


class StarredPaper(Base):
    __tablename__ = "starred_papers"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    user_note = Column(Text, nullable=True, default="")
    tags = Column(String(500), nullable=True, default="")
    starred_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="starred_papers")
    paper = relationship("Paper", back_populates="starred_by")
