# expense_agent/nodes.py
# ─────────────────────────────────────────────────────────────────────────────
# All five graph node functions.
#
# ROUTING CONVENTION
#   route_expense returns Event(route="auto") or Event(route="review").
#   Edges in agent.py use those string keys.
#
# HITL PATTERN
#   llm_risk_review yields a RequestInput (pauses the workflow).
#   On resume, record_outcome reads ctx.resume_inputs[interrupt_id].
#   That node is wired AFTER llm_risk_review with an unconditional edge.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any

from google import genai
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput

from .config import APPROVAL_THRESHOLD, REVIEW_MODEL
from .models import ApprovalDecision, ApprovalOutcome, ExpenseReport

logger = logging.getLogger(__name__)

# ── Shared interrupt ID ────────────────────────────────────────────────────────
# A stable ID lets the resume machinery match the right RequestInput → response.
HUMAN_INTERRUPT_ID = "expense_human_approval"
SECURITY_HUMAN_INTERRUPT_ID = "security_human_approval"


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — parse_expense
# ─────────────────────────────────────────────────────────────────────────────

def parse_expense(ctx: Context, node_input: Any) -> None:
    """Decode the incoming event and write the structured expense to shared state.

    Accepts two formats:
      • Pub/Sub-style: {"data": "<base64-encoded JSON>"}
      • Local-test:   {"data": {"amount": ..., "submitter": ..., ...}}
                   or the expense dict at the top level.

    Writes ctx.state["expense"] (dict) for downstream nodes.
    """
    # On workflow resume, the entry node gets triggered with the resume event (human response).
    # Since the expense is already parsed and stored in state, we skip parsing to avoid validation errors.
    is_resume = False
    if "expense" in ctx.state:
        parent_resume = getattr(ctx.parent_ctx, "resume_inputs", {}) if ctx.parent_ctx else {}
        if ctx.resume_inputs or parent_resume or HUMAN_INTERRUPT_ID in parent_resume or SECURITY_HUMAN_INTERRUPT_ID in parent_resume:
            is_resume = True
        else:
            # Inspect node_input to see if it is a decision payload instead of an expense payload
            temp_payload = None
            if hasattr(node_input, "parts"):
                try:
                    raw_text = "".join(p.text for p in node_input.parts if p.text)
                    temp_payload = json.loads(raw_text)
                except Exception:
                    pass
            elif isinstance(node_input, str):
                try:
                    temp_payload = json.loads(node_input)
                except Exception:
                    pass
            else:
                temp_payload = node_input or {}
            
            if isinstance(temp_payload, dict):
                data_content = temp_payload.get("data", temp_payload)
                if isinstance(data_content, dict) and "decision" in data_content:
                    is_resume = True
                    # Capture the fake resume payload into ctx.state
                    ctx.state["human_response"] = data_content

    if is_resume:
        logger.info("Resuming workflow: skipping expense parsing as it is already stored in state.")
        return

    # If it's a NEW expense, clear any leftover state from a previous run
    for key in ["human_response", "risk_summary", "security_flagged", "redacted_categories"]:
        if key in ctx.state:
            ctx.state[key] = None
    # node_input may be a Content object (user typed it in the playground) or a dict.
    if hasattr(node_input, "parts"):
        # Extract text from a Content object and parse as JSON.
        raw_text = "".join(p.text for p in node_input.parts if p.text)
        payload = json.loads(raw_text)
    elif isinstance(node_input, str):
        payload = json.loads(node_input)
    else:
        payload = node_input or {}

    # Unwrap the "data" envelope if present.
    data = payload.get("data", payload)
    if isinstance(data, str):
        # Base64-encoded JSON (real Pub/Sub message).
        data = json.loads(base64.b64decode(data).decode())

    expense = ExpenseReport(**data)
    ctx.state["expense"] = expense.model_dump()
    logger.info("Parsed expense: %s $%.2f from %s", expense.category, expense.amount, expense.submitter)


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — route_expense  (pure Python, NO LLM)
# ─────────────────────────────────────────────────────────────────────────────

def route_expense(ctx: Context) -> Event:
    """Apply the dollar threshold rule and emit a route signal.

    Under APPROVAL_THRESHOLD  → route "auto"  (auto_approve node)
    At or above threshold     → route "review" (llm_risk_review node)

    The route string must match the Edge(route=...) values in agent.py.
    """
    expense = ExpenseReport(**ctx.state["expense"])
    if expense.amount < APPROVAL_THRESHOLD:
        logger.info("Amount $%.2f < threshold $%.2f -> auto-approve", expense.amount, APPROVAL_THRESHOLD)
        return Event(route="auto")
    else:
        logger.info("Amount $%.2f >= threshold $%.2f -> LLM review", expense.amount, APPROVAL_THRESHOLD)
        return Event(route="review")


# ─────────────────────────────────────────────────────────────────────────────
# Node 3 — auto_approve  (terminal — no outgoing edges)
# ─────────────────────────────────────────────────────────────────────────────

def auto_approve(ctx: Context) -> ApprovalOutcome:
    """Stamp APPROVED instantly — no LLM, no human needed."""
    expense = ExpenseReport(**ctx.state["expense"])
    outcome = ApprovalOutcome(
        message=f"✅ SUCCESS: Expense of ${expense.amount:.2f} for {expense.submitter} was automatically approved!",
        expense=expense, 
        status="APPROVED"
    )
    ctx.state["outcome"] = outcome.model_dump()
    logger.info("AUTO-APPROVED: %s $%.2f", expense.category, expense.amount)
    return outcome


# ─────────────────────────────────────────────────────────────────────────────
# Node 4 — llm_risk_review  (rerun_on_resume=True — see agent.py)
# ─────────────────────────────────────────────────────────────────────────────

def llm_risk_review(ctx: Context):
    """LLM assesses risk, then pauses the workflow for a human decision.

    This is a generator function: it yields a RequestInput which interrupts
    the workflow.  Because the node is declared with rerun_on_resume=True,
    the framework re-executes the whole function on resume.  The resumed run
    checks ctx.resume_inputs for the human's answer and, if found, returns
    immediately so the edge to record_outcome is followed.

    The actual HITL read + recording happens in the NEXT node (record_outcome)
    which receives the human's response as its node_input.
    """
    # ── On resume: the human has already replied — skip LLM and pass through ──
    human_response = ctx.resume_inputs.get(HUMAN_INTERRUPT_ID)
    if human_response is None and "human_response" in ctx.state:
        human_response = ctx.state["human_response"]
        
    if human_response is not None:
        # Store the human decision so record_outcome can read it from state.
        ctx.state["human_response"] = human_response
        return  # triggers the unconditional edge → record_outcome

    # ── First run: call the LLM ───────────────────────────────────────────────
    expense = ExpenseReport(**ctx.state["expense"])

    prompt = f"""You are an expense-approval risk analyst.
Review the following expense and identify any risk factors.

Expense details:
- Submitter : {expense.submitter}
- Amount    : ${expense.amount:.2f}
- Category  : {expense.category}
- Description: {expense.description}
- Date      : {expense.date}

In 2-4 sentences, summarise the key risk factors a human approver should
consider (unusual amount, vague description, policy concerns, etc.).
Be concise and factual."""

    client = genai.Client()
    response = client.models.generate_content(model=REVIEW_MODEL, contents=prompt)
    risk_summary = response.text.strip()
    ctx.state["risk_summary"] = risk_summary
    logger.info("LLM risk summary: %s", risk_summary)

    # ── Pause: ask the human ──────────────────────────────────────────────────
    yield RequestInput(
        interrupt_id=HUMAN_INTERRUPT_ID,
        message=(
            f"⚠️ Expense Requires Approval\n\n"
            f"Submitter : {expense.submitter}\n"
            f"Amount    : ${expense.amount:.2f}\n"
            f"Category  : {expense.category}\n"
            f"Description: {expense.description}\n\n"
            f"Risk Analysis:\n{risk_summary}\n\n"
            f"Please approve or reject this expense."
        ),
        response_schema=ApprovalDecision,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Node 5 — record_outcome  (terminal — no outgoing edges)
# ─────────────────────────────────────────────────────────────────────────────

def record_outcome(ctx: Context) -> ApprovalOutcome:
    """Read the human's decision from state and record the final outcome."""
    expense = ExpenseReport(**ctx.state["expense"])
    risk_summary = ctx.state.get("risk_summary", "")
    security_flagged = ctx.state.get("security_flagged", False)
    redacted_categories = ctx.state.get("redacted_categories", [])

    # human_response was stored by llm_risk_review or security_human_review on its resumed run.
    raw = ctx.state.get("human_response", {})
    if isinstance(raw, dict):
        decision_obj = ApprovalDecision(**raw)
    else:
        decision_obj = raw  # already an ApprovalDecision

    status = "APPROVED" if decision_obj.decision == "approve" else "REJECTED"
    icon = "✅ SUCCESS" if status == "APPROVED" else "❌ REJECTED"
    outcome = ApprovalOutcome(
        message=f"{icon}: Expense of ${expense.amount:.2f} for {expense.submitter} was manually {status.lower()} by reviewer.",
        expense=expense,
        status=status,
        risk_summary=risk_summary if not security_flagged else "Skipped LLM review due to security flagging",
        reviewer_reason=decision_obj.reason,
        security_flagged=security_flagged,
        redacted_categories=redacted_categories,
    )
    ctx.state["outcome"] = outcome.model_dump()
    logger.info(
        "HUMAN DECISION — %s: %s $%.2f | reason: %s | security_flagged: %s | redacted: %s",
        status, expense.category, expense.amount, decision_obj.reason, security_flagged, redacted_categories
    )
    return outcome


# ─────────────────────────────────────────────────────────────────────────────
# Node 6 — security_checkpoint
# ─────────────────────────────────────────────────────────────────────────────

def security_checkpoint(ctx: Context) -> Event:
    """Security Checkpoint Node:
    1. Scrubs SSNs and Credit Cards from the expense description.
    2. Checks for prompt injection.

    Routes to 'clean' or 'flagged'.
    """
    expense_dict = dict(ctx.state["expense"])
    desc = expense_dict.get("description", "")

    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    cc_pattern = r'\b(?:\d[ -]*?){13,19}\b'

    redacted_categories = []

    # Check and scrub SSN
    if re.search(ssn_pattern, desc):
        redacted_categories.append("SSN")
        desc = re.sub(ssn_pattern, "[REDACTED_SSN]", desc)

    # Check and scrub CC (to prevent false positives, we check if the matched sequence parses to digits and has length 13-19)
    def cc_replacer(match):
        digits = re.sub(r'[^0-9]', '', match.group(0))
        if 13 <= len(digits) <= 19:
            redacted_categories.append("Credit Card")
            return "[REDACTED_CC]"
        return match.group(0)

    desc = re.sub(cc_pattern, cc_replacer, desc)

    # Update description in state so downstream nodes see the scrubbed version
    expense_dict["description"] = desc
    ctx.state["expense"] = expense_dict

    # Deduplicate redacted categories and store in state
    redacted_categories = list(set(redacted_categories))
    ctx.state["redacted_categories"] = redacted_categories

    # 2. Defend against prompt injection
    injection_triggers = [
        "ignore prior instructions",
        "ignore previous instructions",
        "ignore rules",
        "ignore the rules",
        "bypass rules",
        "bypass the rules",
        "auto-approve",
        "autoapprove",
        "override rules",
        "override the rules",
        "system prompt",
        "new instructions"
    ]

    is_injection = any(trigger in desc.lower() for trigger in injection_triggers)

    if is_injection:
        logger.warning("Security alert: Prompt injection attempt detected in description!")
        ctx.state["security_flagged"] = True
        return Event(route="flagged")
    else:
        ctx.state["security_flagged"] = False
        return Event(route="clean")


# ─────────────────────────────────────────────────────────────────────────────
# Node 7 — security_human_review (rerun_on_resume=True)
# ─────────────────────────────────────────────────────────────────────────────

def security_human_review(ctx: Context):
    """Flagged Review: Yields a warning about prompt injection and requests human review."""
    # On resume: the human has replied
    human_response = ctx.resume_inputs.get(SECURITY_HUMAN_INTERRUPT_ID)
    if human_response is None and "human_response" in ctx.state:
        human_response = ctx.state["human_response"]
        
    if human_response is not None:
        ctx.state["human_response"] = human_response
        return

    expense = ExpenseReport(**ctx.state["expense"])

    # Yield RequestInput to pause and show warning
    yield RequestInput(
        interrupt_id=SECURITY_HUMAN_INTERRUPT_ID,
        message=(
            f"🚨 SECURITY ALERT: Prompt Injection Attempt Blocked 🚨\n\n"
            f"This expense description triggered our prompt injection defense and was blocked from LLM processing.\n\n"
            f"Submitter : {expense.submitter}\n"
            f"Amount    : ${expense.amount:.2f}\n"
            f"Category  : {expense.category}\n"
            f"Description: {expense.description}\n\n"
            f"Security Status: FLAGGED\n\n"
            f"Please approve or reject this expense."
        ),
        response_schema=ApprovalDecision,
    )
