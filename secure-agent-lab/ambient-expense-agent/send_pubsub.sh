#!/usr/bin/env bash
# ---------------------------------------------------------
# send_pubsub.sh
# Sends a single Pub/Sub‑style webhook request to the
# Ambient Expense Agent running at http://localhost:8080
#
# Usage:   ./send_pubsub.sh   (no arguments needed)
# ---------------------------------------------------------

# ==== 1️⃣  Define the expense payload (as a compact JSON string) ====
expense_json='{
  "amount": 45,
  "submitter": "bob@company.com",
  "category": "meals",
  "description": "Team lunch",
  "date": "2026-04-12"
}'

# ==== 2️⃣  Base‑64‑encode the JSON.
#   - printf %s removes any trailing newline.
#   - base64 -w0 forces a single line (no line‑wrapping).
#   - If your base64 does NOT understand -w0, fall back to:
#         expense_b64=$(printf '%s' "$expense_json" | base64 | tr -d '\n')
expense_b64=$(printf '%s' "$expense_json" | base64 -w0)

# ==== 3️⃣  Assemble the Pub/Sub envelope.
#   All inner double‑quotes are escaped (\"), then Bash expands $expense_b64.
payload="{\"message\":{\"data\":\"$expense_b64\",\"attributes\":{\"source\":\"test\"}},\"subscription\":\"test-sub-11\"}"

# ==== 4️⃣  Target URL (adjust if you run the server on a different port)
endpoint="http://localhost:8080/apps/expense_agent/trigger/pubsub"

# ==== 5️⃣  Fire the request with curl.
#   -s  : silent (no progress meter)
#   -H  : set Content‑Type header
#   -d  : request body
response=$(curl -s "$endpoint" \
  -H "Content-Type: application/json" \
  -d "$payload")

# ==== 6️⃣  Print the server’s JSON response (pretty‑printed with jq if available)
if command -v jq >/dev/null 2>&1; then
  echo "$response" | jq .
else
  echo "$response"
fi

