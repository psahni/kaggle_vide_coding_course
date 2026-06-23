from __future__ import annotations

import os
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import ToolContext
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.workflow import Workflow
from pydantic import BaseModel, Field

# Retrieve API key dynamically from environment variable to mitigate hardcoding vulnerability
model = Gemini(model="gemini-3.1-flash-lite", api_key=os.environ.get("GEMINI_API_KEY"))

# In-memory discount redemption store (simulating database state)
DISCOUNT_STORE: dict[str, bool] = {"WELCOME50": False, "SUMMER20": False}

# In-memory loyalty points store (simulating database state)
LOYALTY_STORE: dict[str, int] = {}

# In-memory cart store (simulating database state)
CART_STORE: dict[str, dict[str, Any]] = {
    "cart_123": {"user_id": "user123", "items": [{"name": "Laptop", "price": 1000.0}], "status": "active"},
    "cart_456": {"user_id": "user456", "items": [{"name": "Shoes", "price": 100.0}], "status": "active"},
    "cart_guest": {"user_id": "guest_789", "items": [{"name": "Book", "price": 20.0}], "status": "active"}
}


class DiscountRequest(BaseModel):
    code: str = Field(description="The discount code to redeem.")
    user_id: str = Field(description="The ID of the user requesting redemption.")


class LoyaltyPointsRequest(BaseModel):
    user_id: str = Field(description="The ID of the user to award points to.")
    points: int = Field(description="The number of points to award. Must be positive.")


class CartCheckoutRequest(BaseModel):
    cart_id: str = Field(description="The ID of the cart to checkout.")
    user_id: str = Field(description="The ID of the user requesting checkout.")
    discount_code: str | None = Field(default=None, description="Optional discount code to apply.")


class UpdateDiscountStatusRequest(BaseModel):
    code: str = Field(description="The discount code to update.")
    active: bool = Field(description="True to activate (make available), False to deactivate (make unavailable).")
    user_id: str = Field(description="The ID of the user requesting this update.")


def redeem_discount(code: str, user_id: str | None = None, tool_context: ToolContext | None = None) -> str:
    """Agent Tool: Redeem a single-use discount code for a user."""
    actual_user_id = tool_context.user_id if tool_context is not None else user_id
    if not actual_user_id or actual_user_id.startswith("guest_"):
        return "Error: Registered user account required to redeem discounts."
    if code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."
    if DISCOUNT_STORE[code]:
        return "Error: Discount code has already been redeemed."

    DISCOUNT_STORE[code] = True
    return f"Success: Discount code {code} redeemed successfully for user {actual_user_id}."


def award_loyalty_points(user_id: str | None = None, points: int = 0, tool_context: ToolContext | None = None) -> str:
    """Agent Tool: Award loyalty points to a user's account after a successful purchase."""
    actual_user_id = tool_context.user_id if tool_context is not None else user_id
    if not actual_user_id or actual_user_id.startswith("guest_"):
        return "Error: Registered user account required to award loyalty points."
    if points <= 0:
        return "Error: Points must be a positive integer."
    if points > 1000:
        return "Error: Cannot award more than 1000 points in a single transaction."

    if actual_user_id not in LOYALTY_STORE:
        LOYALTY_STORE[actual_user_id] = 0
    LOYALTY_STORE[actual_user_id] += points

    return f"Success: Awarded {points} loyalty points to user {actual_user_id}. New balance: {LOYALTY_STORE[actual_user_id]}."


def process_cart_checkout(cart_id: str, user_id: str | None = None, discount_code: str | None = None, tool_context: ToolContext | None = None) -> str:
    """Agent Tool: Process the checkout for a cart, optionally applying a discount code."""
    actual_user_id = tool_context.user_id if tool_context is not None else user_id
    if cart_id not in CART_STORE:
        return "Error: Cart not found."

    cart = CART_STORE[cart_id]
    if cart["user_id"] != actual_user_id:
        return "Error: Unauthorized checkout. Cart owner mismatch."

    if cart["status"] != "active":
        return "Error: Cart has already been checked out."

    subtotal = sum(item["price"] for item in cart["items"])
    final_total = subtotal

    if discount_code:
        if discount_code not in DISCOUNT_STORE:
            return "Error: Invalid discount code."
        if DISCOUNT_STORE[discount_code]:
            return "Error: Discount code has already been redeemed."
        if not actual_user_id or actual_user_id.startswith("guest_"):
            return "Error: Registered user account required to redeem discounts."

        if discount_code == "WELCOME50":
            final_total = subtotal * 0.5
        elif discount_code == "SUMMER20":
            final_total = subtotal * 0.8

        DISCOUNT_STORE[discount_code] = True

    cart["status"] = "completed"

    discount_str = f" with discount {discount_code}" if discount_code else ""
    return f"Success: Checkout complete for cart {cart_id}{discount_str}. Total paid: ${final_total:.2f}."


def update_discount_status(code: str, active: bool, user_id: str | None = None, tool_context: ToolContext | None = None) -> str:
    """Agent Tool: Allows administrators to activate or deactivate discount codes in the store."""
    actual_user_id = tool_context.user_id if tool_context is not None else user_id
    if not actual_user_id or not actual_user_id.startswith("admin_"):
        return "Error: Administrator privileges required to update discount status."

    if code not in DISCOUNT_STORE:
        return "Error: Discount code not found."

    DISCOUNT_STORE[code] = not active
    status_str = "activated" if active else "deactivated"
    return f"Success: Discount code {code} has been successfully {status_str}."


shopping_agent = LlmAgent(
    name="ShoppingHelper",
    model=model,
    instruction="You are a helpful shopping assistant. Use your tools to redeem discount codes, award loyalty points, process cart checkouts, and update discount statuses for users.",
    tools=[redeem_discount, award_loyalty_points, process_cart_checkout, update_discount_status],
)

root_workflow = Workflow(
    name="shopping_assistant_workflow", edges=[("START", shopping_agent)]
)

app = App(name="shopping_assistant", root_agent=root_workflow)

# Compatibility with existing integration tests
root_agent = root_workflow
