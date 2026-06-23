# expense_agent/models.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Pydantic models used as typed contracts between graph nodes.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ExpenseReport(BaseModel):
    """Structured expense data extracted from the incoming event."""

    amount: float = Field(..., description="Expense amount in USD")
    submitter: str = Field(..., description="Name or ID of the person who submitted")
    category: str = Field(..., description="Expense category, e.g. Travel, Software")
    description: str = Field(..., description="Brief description of the expense")
    date: str = Field(..., description="Date of expense in YYYY-MM-DD or similar")


class ApprovalDecision(BaseModel):
    """The human reviewer's decision, used as the RequestInput response schema."""

    decision: Literal["approve", "reject"] = Field(
        ..., description="Whether to approve or reject the expense"
    )
    reason: str = Field(
        ..., description="Short explanation for the decision (required)"
    )


class ApprovalOutcome(BaseModel):
    """Final outcome recorded at the end of the workflow."""

    message: Optional[str] = None  # Friendly confirmation message for the playground
    expense: ExpenseReport
    status: Literal["APPROVED", "REJECTED"]
    risk_summary: Optional[str] = None   # Only present for reviewed expenses
    reviewer_reason: Optional[str] = None  # Only present for human-reviewed expenses
    security_flagged: Optional[bool] = False
    redacted_categories: Optional[list[str]] = None
