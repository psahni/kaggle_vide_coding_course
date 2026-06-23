import logging
import os
import sys

from fastapi import FastAPI, Request
from google.adk.runners import InMemoryRunner
from google.genai import types
import json

from expense_agent.agent import app as adk_app

# - Telemetry: Set otel_to_cloud=False
os.environ["OTEL_TO_CLOUD"] = "False"

# - Logging: Use standard Python logging for console logs.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ambient Expense Agent")

# Initialize shared InMemoryRunner on startup (private to this module)
@app.on_event("startup")
async def _init_runner():
    # Store the runner in FastAPI's state for reuse across requests
    app.state.runner = InMemoryRunner(agent=adk_app.root_agent)

@app.post("/apps/expense_agent/trigger/pubsub")
async def handle_pubsub(request: Request):
    payload = await request.json()
    message = payload.get("message", {})
    subscription = payload.get("subscription", "")
    
    # Normalize subscription path to short name
    session_id = subscription.split("/")[-1] if subscription else "default-session"
    logger.info(f"Received Pub/Sub message from subscription: {session_id}")
    
    # Get base64 encoded data
    data_b64 = message.get("data", "")
    
    # Use shared runner instance

    # Ensure a clean session for this subscription.
    # If a session with the same ID already exists we delete it first.
    try:
        await app.state.runner.session_service.delete_session(
            app_name=app.state.runner.app_name,
            user_id="pubsub",
            session_id=session_id,
        )
    except Exception:
        # It's fine if the session didn't exist.
        pass

    # Now create a fresh session record.
    await app.state.runner.session_service.create_session(
        app_name=app.state.runner.app_name,
        user_id="pubsub",
        session_id=session_id,
    )



    # Build a Content object — parse_expense already handles {"data": "<b64>"}.
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=json.dumps({"data": data_b64}))]
    )

    # Run the workflow asynchronously.
    try:
        async for _ in app.state.runner.run_async(
            user_id="pubsub",
            session_id=session_id,
            new_message=content,
        ):
            pass
        logger.info(f"Workflow completed for session: {session_id}")
    except Exception as e:
        logger.error(f"Workflow failed for session {session_id}: {e}")
        return {"status": "error", "error": str(e)}

    # Fetch the final session state to see the outcome
    session = await app.state.runner.session_service.get_session(
        app_name=app.state.runner.app_name,
        user_id="pubsub",
        session_id=session_id,
    )

    response = {"status": "success"}
    if session and session.state:
        outcome = session.state.get("outcome")
        if outcome:
            response["workflow_status"] = "COMPLETED"
            response["outcome"] = outcome
        else:
            response["workflow_status"] = "SUSPENDED"
            response["message"] = "Expense requires human review/approval."
    
    return response


@app.get("/apps/expense_agent/sessions/{session_id}")
async def get_session_state(session_id: str):
    session = await app.state.runner.session_service.get_session(
        app_name=app.state.runner.app_name,
        user_id="pubsub",
        session_id=session_id,
    )
    if not session:
        return {"status": "error", "message": "Session not found"}
    return {
        "status": "success",
        "session_id": session_id,
        "state": session.state,
    }


