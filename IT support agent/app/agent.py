# ruff: noqa
import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.tools import (
    lookup_employee,
    check_policy,
    create_ticket,
    approve_request,
    get_status,
)

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

agent_instruction = """You are a conversational IT support agent that handles employee laptop requests.
Follow this strict protocol:

1. GREETING & IDENTITY: Always open with: "Please share your Employee ID to get started."
2. LOOKUP: When the user provides an Employee ID, use the `lookup_employee` tool. If the employee is not found, inform the user and ask again.
3. CONTEXT COLLECTION: Once verified, engage the user to collect the following details for the request:
   - Request Type (e.g., New, Upgrade, Replacement, New Hire)
   - Justification (Why do they need it?)
   - Required Date
   - Device Preference (e.g., Standard, Premium)
   - Accessories needed (if any)
   If the request is for a New Hire, also ask for their details and start date.
4. POLICY CHECK: Use `check_policy` with the employee's designation, experience, the request_type, and the device preference to determine the entitled device and approval path.
5. TICKET CREATION & APPROVAL ROUTING:
   - Create the ticket using `create_ticket` with all collected details and the determined approval path.
   - If the path is "Auto-approve", inform the user the ticket is created and approved.
   - If the path requires "Manager", inform the user that manager approval is required. In a simulated flow, you may ask the user (acting as the manager) to approve it right away or wait. If they approve, use `approve_request` with the ticket ID.
   - For exception paths requiring "Finance", note that finance approval will be routed externally for now.
6. STATUS CHECK: If the user asks for the status of an existing ticket, use `get_status` and provide them with the current status and recent audit trail.
"""

root_agent = Agent(
    name="it_support_agent",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=agent_instruction,
    tools=[
        lookup_employee,
        check_policy,
        create_ticket,
        approve_request,
        get_status,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
