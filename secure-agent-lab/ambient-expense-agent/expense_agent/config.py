# expense_agent/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central config — change threshold and model here, nowhere else.
# ─────────────────────────────────────────────────────────────────────────────

# Expenses BELOW this threshold are auto-approved without involving any LLM.
# Expenses AT or ABOVE this threshold go through LLM risk review + human sign-off.
APPROVAL_THRESHOLD: float = 100.0

REVIEW_MODEL: str = "gemini-3.1-flash-lite"
