#!/usr/bin/env python3
"""
test_pubsub.py

A utility script to test the local ambient expense agent's Pub/Sub webhook endpoint.
This script formats the expense data, base64-encodes it (as GCP Pub/Sub does),
sends the HTTP POST request to the local server, and displays the response.
"""

import base64
import json
import urllib.request
from typing import Any, Dict


def encode_payload(data: Dict[str, Any]) -> str:
    """
    Serializes a dictionary payload to JSON and encodes it to base64.

    Args:
        data: The raw dictionary payload representing the expense report.

    Returns:
        A base64-encoded ASCII string.
    """
    json_bytes = json.dumps(data).encode("utf-8")
    base64_bytes = base64.b64encode(json_bytes)
    return base64_bytes.decode("ascii")


def send_pubsub_message(
    endpoint_url: str, data_b64: str, subscription: str
) -> Dict[str, Any]:
    """
    Sends a simulated GCP Pub/Sub push notification to the webhook endpoint.

    Args:
        endpoint_url: The target HTTP URL of the webhook (e.g., http://127.0.0.1:8080/).
        data_b64: The base64-encoded payload string.
        subscription: The fully-qualified GCP subscription identifier.

    Returns:
        The deserialized JSON response dictionary from the server.
    """
    # Construct the Pub/Sub envelope schema
    payload = {
        "message": {
            "data": data_b64,
        },
        "subscription": subscription,
    }

    # Encode the request payload as JSON bytes
    request_data = json.dumps(payload).encode("utf-8")

    # Set up the HTTP Request with the appropriate content type header
    req = urllib.request.Request(
        endpoint_url,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Perform the synchronous HTTP call and return the parsed JSON response
    with urllib.request.urlopen(req) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def main() -> None:
    # Target URL of the local ambient expense server
    endpoint_url = "http://localhost:8080/apps/expense_agent/trigger/pubsub"

    # Test expense data matching the prompt requirements
    test_expense = {
        "amount": 150.0,
        "submitter": "alice@company.com",
        "category": "software",
        "description": "IDE License",
        "date": "2026-06-06",
    }

    # Simulated GCP Pub/Sub subscription name
    subscription = "projects/test/subscriptions/my-sub-1"

    print("--- Simulating Pub/Sub Webhook Trigger ---")
    print(f"Target URL:   {endpoint_url}")
    print(f"Subscription: {subscription}")
    print(f"Expense Data: {test_expense}")

    try:
        # 1. Base64-encode the raw data payload
        b64_data = encode_payload(test_expense)
        print(f"Encoded Data: {b64_data}")

        # 2. Post the payload to the server
        print("\nSending request...")
        result = send_pubsub_message(endpoint_url, b64_data, subscription)

        print("\n--- Response Received ---")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")


if __name__ == "__main__":
    main()
