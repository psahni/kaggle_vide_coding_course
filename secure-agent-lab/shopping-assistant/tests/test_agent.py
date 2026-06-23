# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Outcome-based security test suite for the shopping assistant agent.
Verifies all security boundaries and business logic guardrails for redeem_discount.
"""

import pytest
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent, DISCOUNT_STORE


def run_agent_prompt(user_id: str, prompt: str) -> str:
    """Helper to run a prompt through the agent and return the concatenated text response."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id=user_id, app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=prompt)]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text


class TestAgentRedeemDiscountSecurity:
    """Outcome-based security test suite verifying redeem_discount boundaries at the agent level."""

    def setup_method(self):
        """Reset discount codes state before each test."""
        for code in DISCOUNT_STORE:
            DISCOUNT_STORE[code] = False

    def test_registered_user_redemption_success(self):
        """Verify that a registered user can successfully redeem a valid discount code."""
        prompt = "Please redeem the discount code WELCOME50 for me."
        user_id = "user123"

        response = run_agent_prompt(user_id=user_id, prompt=prompt)

        # Verify store state changes
        assert DISCOUNT_STORE["WELCOME50"] is True
        # Verify agent communicates success
        assert "success" in response.lower() or "redeemed" in response.lower()

    def test_guest_user_redemption_rejection(self):
        """Verify that a guest user is blocked from redeeming discounts."""
        prompt = "Redeem discount code WELCOME50."
        user_id = "guest_123"

        response = run_agent_prompt(user_id=user_id, prompt=prompt)

        # Verify store state did NOT change
        assert DISCOUNT_STORE["WELCOME50"] is False
        # Verify agent communicates the error / block or requests account details
        assert any(k in response.lower() for k in ["guest", "registered", "error", "provide", "account", "user id"])

    def test_invalid_code_redemption_rejection(self):
        """Verify that an invalid discount code is rejected."""
        prompt = "Please redeem the discount code INVALID99."
        user_id = "user123"

        response = run_agent_prompt(user_id=user_id, prompt=prompt)

        # Verify invalid code is not added or redeemed
        assert "INVALID99" not in DISCOUNT_STORE
        # Verify agent communicates the error
        assert "invalid" in response.lower() or "error" in response.lower()

    def test_duplicate_redemption_rejection(self):
        """Verify that the same discount code cannot be redeemed twice."""
        prompt = "Please redeem discount WELCOME50."
        user_id = "user123"

        # First redemption should succeed
        response1 = run_agent_prompt(user_id=user_id, prompt=prompt)
        assert DISCOUNT_STORE["WELCOME50"] is True
        assert "success" in response1.lower() or "redeemed" in response1.lower()

        # Second redemption should fail
        response2 = run_agent_prompt(user_id=user_id, prompt=prompt)
        assert "already" in response2.lower() or "redeemed" in response2.lower() or "error" in response2.lower()
