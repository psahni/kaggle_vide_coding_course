# expense_agent/agent.py
# ─────────────────────────────────────────────────────────────────────────────
# ADK 2.0 Graph Workflow — Ambient Expense-Approval Agent
#
# Graph wired here; all node logic lives in nodes.py.
# Config (threshold + model) lives in config.py.
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root — override=True beats any stale env vars.
# The SDK reads GOOGLE_API_KEY from the environment automatically.
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from google.adk.apps import App
from google.adk.workflow import Edge, FunctionNode, START, Workflow

from .nodes import (
    auto_approve,
    llm_risk_review,
    parse_expense,
    record_outcome,
    route_expense,
    security_checkpoint,
    security_human_review,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Wrap every function as a named FunctionNode.
# ─────────────────────────────────────────────────────────────────────────────

parse_node = FunctionNode(func=parse_expense, name="parse_expense")

route_node = FunctionNode(func=route_expense, name="route_expense")

auto_node = FunctionNode(func=auto_approve, name="auto_approve")

# rerun_on_resume=True → the framework re-executes llm_risk_review after the
# human responds.  The second run reads ctx.resume_inputs[HUMAN_INTERRUPT_ID]
# and exits immediately so the edge to record_outcome is followed.
review_node = FunctionNode(
    func=llm_risk_review,
    name="llm_risk_review",
    rerun_on_resume=True,
)

checkpoint_node = FunctionNode(func=security_checkpoint, name="security_checkpoint")

security_human_node = FunctionNode(
    func=security_human_review,
    name="security_human_review",
    rerun_on_resume=True,
)

outcome_node = FunctionNode(func=record_outcome, name="record_outcome")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Wire the graph with Edges.
#
#  START ──► parse_expense ──► security_checkpoint
#                                       │
#                                       ├──────(route="clean")───────┐
#                                       ▼                            ▼
#                              security_human_review           route_expense
#         (route="flagged")             │                            │
#                                       │              ┌─────────────┴────────────┐
#                                       │       (route="auto")             (route="review")
#                                       │              ▼                          ▼
#                                       │         auto_approve             llm_risk_review
#                                       │         (terminal)                      │
#                                       └────────────────────────┬────────────────┘
#                                                                ▼
#                                                          record_outcome
#                                                            (terminal)
# ─────────────────────────────────────────────────────────────────────────────

expense_workflow = Workflow(
    name="expense_approval_workflow",
    edges=[
        # Entry: START → parse → security_checkpoint
        (START, parse_node, checkpoint_node),

        # Conditional fork from security_checkpoint:
        #   "clean"   → route_expense (only clean expenses get routed)
        #   "flagged" → security_human_review (bypass routing completely)
        Edge(from_node=checkpoint_node, to_node=route_node, route="clean"),
        Edge(from_node=checkpoint_node, to_node=security_human_node, route="flagged"),

        # Conditional fork from route_expense:
        #   "auto"   → auto_approve   (terminal — no further edges)
        #   "review" → llm_risk_review
        Edge(from_node=route_node, to_node=auto_node,    route="auto"),
        Edge(from_node=route_node, to_node=review_node, route="review"),

        # After reviews pause + resume → record the final outcome (terminal)
        Edge(from_node=review_node, to_node=outcome_node),
        Edge(from_node=security_human_node, to_node=outcome_node),
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Expose as an ADK App so `adk web expense_agent` works.
# ─────────────────────────────────────────────────────────────────────────────

app = App(
    root_agent=expense_workflow,
    name="expense_agent",
)
