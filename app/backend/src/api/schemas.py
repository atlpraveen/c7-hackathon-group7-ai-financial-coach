"""Pydantic request/response models for the API.

Uses ``typing`` unions (Optional/Dict/List) rather than ``X | None`` so the
models evaluate on Python 3.9+ as well as 3.11 (the Docker target).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class Debt(BaseModel):
    name: str
    balance: float = Field(ge=0)
    interest_rate: float = Field(ge=0, description="Annual APR, percent")
    min_payment: float = Field(ge=0, default=0)


class Goal(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    months: int = Field(gt=0, default=12)
    current: float = Field(ge=0, default=0)
    annual_return: float = Field(ge=0, default=0)


class ProfileInput(BaseModel):
    """User-supplied financial profile. All fields optional — anything omitted
    falls back to values derived from uploaded documents, then to defaults."""

    monthly_income: Optional[float] = Field(default=None, ge=0)
    monthly_expenses: Optional[float] = Field(default=None, ge=0)
    expenses_by_category: Optional[Dict[str, float]] = None
    debts: Optional[List[Debt]] = None
    savings_balance: Optional[float] = Field(default=None, ge=0)
    investment_balance: Optional[float] = Field(default=None, ge=0)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    risk_tolerance: Optional[str] = Field(
        default=None, description="conservative | moderate | aggressive"
    )
    goals: Optional[List[Goal]] = None


class AgentRequest(BaseModel):
    """Generic body for the per-agent endpoints."""

    profile_overrides: Optional[ProfileInput] = None
    params: Dict = Field(default_factory=dict)


class CoachRequest(BaseModel):
    query: Optional[str] = None
    profile_overrides: Optional[ProfileInput] = None
    params: Dict = Field(default_factory=dict)
    conversation_id: Optional[int] = None


class AskRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict


# --------------------------------------------------------------------------- #
# Goals (financial goal tracking)
# --------------------------------------------------------------------------- #
class GoalInput(BaseModel):
    name: str
    category: str = "general"
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0)
    monthly_contribution: float = Field(ge=0, default=0)
    target_months: int = Field(gt=0, default=12)
    annual_return: float = Field(ge=0, default=0)


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    target_amount: Optional[float] = Field(default=None, gt=0)
    current_amount: Optional[float] = Field(default=None, ge=0)
    monthly_contribution: Optional[float] = Field(default=None, ge=0)
    target_months: Optional[int] = Field(default=None, gt=0)
    annual_return: Optional[float] = Field(default=None, ge=0)


# --------------------------------------------------------------------------- #
# Transaction categorization
# --------------------------------------------------------------------------- #
class CategorizeRequest(BaseModel):
    """Categorize ad-hoc descriptions; if omitted, the user's stored
    transactions are categorized."""

    descriptions: Optional[List[str]] = None
    use_llm: bool = True


class RecategorizeRequest(BaseModel):
    transaction_id: int
    category: str
