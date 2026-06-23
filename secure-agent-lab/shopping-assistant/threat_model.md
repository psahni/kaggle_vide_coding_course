# STRIDE Threat Model Assessment: Shopping Assistant Agent

This document provides a systematic STRIDE threat modeling assessment of the `shopping-assistant` agent graph and architecture based on `app/agent.py` and `app/agent_runtime_app.py`.

---

## 1. System Boundaries & Architecture

*   **Entry Points:**
    *   **User Input Interface:** Handled via the ADK `Runner` and `AgentEngineApp` (subclassing `AdkApp`), exposing `async_stream_query` endpoints.
    *   **Agent Workflow:** The top-level `App` routes messages to the root `Workflow` (`shopping_assistant_workflow`) which triggers the `LlmAgent` (`ShoppingHelper`).
*   **Trust Boundaries:**
    *   Boundary between the external client (user message) and the agent runtime environment.
    *   Boundary between the `LlmAgent` and the tool execution runtime.
*   **Data Stores:**
    *   `DISCOUNT_STORE`: An in-memory dict mapping discount codes to redemption status (`{"WELCOME50": False, "SUMMER20": False}`).

---

## 2. STRIDE Evaluation

### 👤 Spoofing (Authenticity)
*   **Threat:** A user could pass a spoofed or arbitrary `user_id` parameter to the API entry point.
*   **Assessment:** The `redeem_discount` tool accepts `user_id: str` directly. Currently, the tool assumes the ID provided by the runner is authentic and performs no cryptographic/session verification.
*   **Mitigation:** Verify `user_id` at the API/Session boundary inside `AgentEngineApp` (using IAM or ID Tokens) before passing it down to the agent context.

### ✍️ Tampering (Integrity)
*   **Threat:** Attackers could bypass validation checks or cause race conditions during discount code redemption.
*   **Assessment:** `DISCOUNT_STORE` is in-memory. If multiple requests arrive concurrently or if the container scales out, race conditions can occur. Also, if the serverless container scales down or restarts, the database state resets to default (`False`), letting users redeem codes multiple times.
*   **Mitigation:** Replace the in-memory `DISCOUNT_STORE` with a persistent transactional database (e.g., Firestore or Cloud SQL) using ACID transactions.

### 📜 Repudiation (Non-repudiation)
*   **Threat:** A user redeems a discount code, but there is no secure audit trail to prove who did it or when.
*   **Assessment:** While redemptions return a string showing success, there is no immutable audit trail logging the events.
*   **Mitigation:** Emit structured security audit logs to Google Cloud Logging whenever `redeem_discount` is successfully called, capturing the timestamp, sanitized `user_id`, and `code`.

### 🔓 Information Disclosure (Confidentiality)
*   **Threat:** Exposure of internal API credentials or sensitive customer data.
*   **Assessment:** The draft configuration of `Gemini` contains a hardcoded mock API key (`api_key="AIzaSyD-mock-key-value-12345"`). While it is a mock key, hardcoding credentials in source code exposes them to exposure in Git repositories.
*   **Mitigation:** Retrieve API keys or credentials dynamically from environment variables or Google Secret Manager at runtime. The custom Semgrep pre-commit hook is already configured to block any such hardcoded values in future commits.

### 🚫 Denial of Service (Availability)
*   **Threat:** Malicious actors sending high-volume requests to exhaust LLM tokens or Vertex AI resources.
*   **Assessment:** There are no rate limits defined on the query interface, which could lead to API rate limits being hit or high billing charges.
*   **Mitigation:** Enforce API rate-limiting and request-size limits at the gateway layer (e.g., Apigee, Cloud Armor) before requests reach the container runtime.

### 🔑 Elevation of Privilege (Authorization)
*   **Threat:** A guest user or unauthorized user triggers privileged discount redemptions.
*   **Assessment:** `redeem_discount` checks if the `user_id` is empty or starts with `"guest_"`, raising an error and preventing unauthorized redemption. Crucially, this authorization check is implemented in the Python tool logic (secure-by-default) rather than relying on LLM instructions, preventing prompt injection bypasses.
*   **Mitigation:** Keep authorization logic implemented in code rather than system prompts, and align the guest user validation with a standardized role check.
