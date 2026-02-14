"""Pydantic request/response schemas."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Subscription ──────────────────────────────────────

class SubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    research_interest: str = Field(..., min_length=1)
    llm_provider: str = Field(..., pattern=r"^(qwen|deepseek)$")
    llm_api_key: str = Field(..., min_length=1)
    llm_model: Optional[str] = None
    arxiv_categories: list[str] = Field(..., min_length=1)
    max_papers: int = Field(default=5, ge=1, le=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_daily: bool = False
    cron_time: Optional[str] = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    research_interest: Optional[str] = None
    llm_provider: Optional[str] = Field(default=None, pattern=r"^(qwen|deepseek)$")
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    arxiv_categories: Optional[list[str]] = None
    max_papers: Optional[int] = Field(default=None, ge=1, le=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_daily: Optional[bool] = None
    cron_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    is_active: Optional[bool] = None


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    name: str
    research_interest: str
    llm_provider: str
    llm_model: Optional[str]
    arxiv_categories: list[str]
    max_papers: int
    start_date: Optional[date]
    end_date: Optional[date]
    auto_daily: bool
    cron_time: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Paper ─────────────────────────────────────────────

class PaperOut(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: str
    abstract: str
    url: str
    pdf_url: str
    categories: Optional[str]
    published_date: Optional[date]

    model_config = {"from_attributes": True}


# ── PushRecord ────────────────────────────────────────

class PushRecordOut(BaseModel):
    id: int
    subscription_id: int
    paper: PaperOut
    relevance_score: float
    relevance_reason: Optional[str]
    abstract_zh: Optional[str]
    pushed_at: datetime

    model_config = {"from_attributes": True}


# ── Star ──────────────────────────────────────────────

class StarCreate(BaseModel):
    paper_id: int
    user_note: Optional[str] = ""
    tags: Optional[str] = ""


class StarUpdate(BaseModel):
    user_note: Optional[str] = None
    tags: Optional[str] = None


class StarredPaperOut(BaseModel):
    id: int
    user_id: int
    paper: PaperOut
    user_note: Optional[str]
    tags: Optional[str]
    starred_at: datetime

    model_config = {"from_attributes": True}


# ── Trigger ───────────────────────────────────────────

class TriggerPushRequest(BaseModel):
    """Manual trigger for a subscription push."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
