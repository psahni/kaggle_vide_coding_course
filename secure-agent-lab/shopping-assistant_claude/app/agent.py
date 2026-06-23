# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# In-memory store for discount codes
# Maps code -> (discount_percentage, redeemed_user_ids)
DISCOUNT_CODES = {
    "WELCOME50": (50, set()),
    "SUMMER20": (20, set()),
    "SAVE30": (30, set()),
}


def redeem_discount_code(code: str, user_id: str) -> str:
    """Redeem a single-use discount code for a registered user.

    Args:
        code: The discount code to redeem (e.g., "WELCOME50").
        user_id: The registered user ID attempting to redeem the code.

    Returns:
        A string indicating success or failure of the redemption attempt.
    """
    code = code.upper().strip()

    if code not in DISCOUNT_CODES:
        return f"Error: Invalid discount code '{code}'. Available codes: WELCOME50, SUMMER20, SAVE30"

    if not user_id or not user_id.strip():
        return "Error: User ID is required to redeem a discount code."

    discount_percentage, redeemed_users = DISCOUNT_CODES[code]

    if user_id in redeemed_users:
        return f"Error: User '{user_id}' has already redeemed code '{code}'. Each code can only be used once per user."

    redeemed_users.add(user_id)
    return f"Success! User '{user_id}' has redeemed code '{code}' for a {discount_percentage}% discount."


def get_available_products() -> str:
    """Get information about currently available products in the store.

    Returns:
        A string with available products and their prices.
    """
    products = {
        "Electronics": {
            "Laptop": "$999",
            "Wireless Mouse": "$29",
            "USB-C Cable": "$15",
        },
        "Clothing": {
            "T-Shirt": "$24",
            "Jeans": "$79",
            "Running Shoes": "$120",
        },
        "Home & Garden": {
            "Coffee Maker": "$89",
            "Desk Lamp": "$45",
            "Plant Pot": "$22",
        },
    }

    result = "Available Products:\n"
    for category, items in products.items():
        result += f"\n{category}:\n"
        for product, price in items.items():
            result += f"  - {product}: {price}\n"
    return result


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        # Explicitly initialized with mock API key for demonstrating pre-commit security gating
        api_key="", # Insert api key here, to check pre-commit hook for security
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI shopping assistant for a retail store. Help customers find products, answer questions about inventory, and assist with redeeming discount codes. Be friendly and professional.",
    tools=[redeem_discount_code, get_available_products],
)

# Note: The hardcoded mock API key above is intentionally insecure for demonstrating
# automated pre-commit security scanning. In production, use Application Default
# Credentials (ADC) or environment variables instead.

app = App(
    root_agent=root_agent,
    name="app",
)
