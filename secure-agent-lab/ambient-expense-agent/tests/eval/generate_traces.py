import json
import re
from pathlib import Path

def redact_pii(text: str) -> bool:
    """Return True if PII was found and redacted (simulated)."""
    # simple regex for phone numbers and emails
    phone_pattern = re.compile(r"\b\d{3}-\d{4}\b")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    return bool(phone_pattern.search(text) or email_pattern.search(text))

def detect_injection(text: str) -> bool:
    return "ignore" in text.lower()

def main():
    dataset_path = Path(__file__).parent / "datasets" / "basic-dataset.json"
    output_path = Path(__file__).parents[2].parent / "artifacts" / "traces" / "generated_traces.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dataset_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    traces = []
    for case in scenarios:
        expense = case["expense"]
        description = expense.get("description", "")
        amount = expense.get("amount", 0)
        pii = redact_pii(description)
        injection = detect_injection(description)
        route = "auto" if amount < 100 else "human"
        approved = route == "auto"
        trace = {
            "eval_case_id": case["id"],
            "prompt": {"parts": [{"text": case["description"]}]},
            "responses": [{"response": {"parts": [{"text": "Approved" if approved else "Rejected"}]}}],
            "description": case["description"],
            "expense": expense,
            "pii_redacted": pii,
            "injection_detected": injection,
            "route": route,
            "approved": approved,
        }
        traces.append(trace)
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"eval_cases": traces}, f, indent=2)
    print(f"Generated {len(traces)} traces to {output_path}")

if __name__ == "__main__":
    main()
