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
Unit tests for shopping assistant tools.
Tests discount code redemption functionality.
"""

from app.agent import DISCOUNT_STORE, redeem_discount, LOYALTY_STORE, award_loyalty_points, CART_STORE, process_cart_checkout, update_discount_status


class TestDiscountCodeRedemption:
    """Test suite for discount code redemption tool."""

    def setup_method(self):
        """Reset discount codes before each test."""
        for code in DISCOUNT_STORE:
            DISCOUNT_STORE[code] = False

    def test_valid_code_redemption(self):
        """Test successful redemption of a valid discount code."""
        result = redeem_discount("WELCOME50", "user123")
        assert "Success" in result
        assert "user123" in result
        assert "WELCOME50" in result

    def test_invalid_code(self):
        """Test that invalid codes are rejected."""
        result = redeem_discount("INVALID99", "user123")
        assert "Error" in result
        assert "Invalid discount code" in result

    def test_duplicate_redemption_prevention(self):
        """Test that the same user/code cannot redeem a code twice."""
        user_id = "user123"

        # First redemption should succeed
        result1 = redeem_discount("WELCOME50", user_id)
        assert "Success" in result1

        # Second redemption should fail
        result2 = redeem_discount("WELCOME50", user_id)
        assert "Error" in result2
        assert "already been redeemed" in result2

    def test_guest_user_rejection(self):
        """Test that guest users are rejected."""
        result = redeem_discount("WELCOME50", "guest_123")
        assert "Error" in result
        assert "Registered user account required" in result

    def test_missing_user_id(self):
        """Test that missing user ID is rejected."""
        result = redeem_discount("WELCOME50", "")
        assert "Error" in result
        assert "Registered user account required" in result

    def test_none_user_id(self):
        """Test that None user ID is handled."""
        result = redeem_discount("WELCOME50", None)
        assert "Error" in result
        assert "Registered user account required" in result

    def test_all_discount_codes_available(self):
        """Test that all expected discount codes are available."""
        expected_codes = {"WELCOME50", "SUMMER20"}
        actual_codes = set(DISCOUNT_STORE.keys())
        assert expected_codes == actual_codes


class TestLoyaltyPoints:
    """Test suite for loyalty points tool."""

    def setup_method(self):
        """Reset loyalty points before each test."""
        LOYALTY_STORE.clear()

    def test_valid_loyalty_points_award(self):
        """Test successful award of loyalty points."""
        result = award_loyalty_points("user123", 100)
        assert "Success" in result
        assert "user123" in result
        assert "100" in result
        assert LOYALTY_STORE["user123"] == 100

        # Award more points to the same user
        result2 = award_loyalty_points("user123", 200)
        assert "Success" in result2
        assert "200" in result2
        assert LOYALTY_STORE["user123"] == 300

    def test_guest_user_rejection(self):
        """Test that guest users are rejected."""
        result = award_loyalty_points("guest_123", 100)
        assert "Error" in result
        assert "Registered user account required" in result
        assert "guest_123" not in LOYALTY_STORE

    def test_missing_user_id(self):
        """Test that missing user ID is rejected."""
        result = award_loyalty_points("", 100)
        assert "Error" in result
        assert "Registered user account required" in result

    def test_none_user_id(self):
        """Test that None user ID is handled."""
        result = award_loyalty_points(None, 100)
        assert "Error" in result
        assert "Registered user account required" in result

    def test_negative_points(self):
        """Test that negative points are rejected."""
        result = award_loyalty_points("user123", -50)
        assert "Error" in result
        assert "Points must be a positive integer" in result
        assert "user123" not in LOYALTY_STORE

    def test_zero_points(self):
        """Test that zero points are rejected."""
        result = award_loyalty_points("user123", 0)
        assert "Error" in result
        assert "Points must be a positive integer" in result
        assert "user123" not in LOYALTY_STORE

    def test_exceeding_max_points_limit(self):
        """Test that awarding more than 1000 points is rejected."""
        result = award_loyalty_points("user123", 1001)
        assert "Error" in result
        assert "Cannot award more than 1000 points" in result
        assert "user123" not in LOYALTY_STORE

    def test_exact_max_points_limit(self):
        """Test that awarding exactly 1000 points is successful."""
        result = award_loyalty_points("user123", 1000)
        assert "Success" in result
        assert LOYALTY_STORE["user123"] == 1000


class TestCartCheckout:
    """Test suite for cart checkout tool."""

    def setup_method(self):
        """Reset cart and discount store states before each test."""
        # Reset CART_STORE state
        CART_STORE.clear()
        CART_STORE.update({
            "cart_123": {"user_id": "user123", "items": [{"name": "Laptop", "price": 1000.0}], "status": "active"},
            "cart_456": {"user_id": "user456", "items": [{"name": "Shoes", "price": 100.0}], "status": "active"},
            "cart_guest": {"user_id": "guest_789", "items": [{"name": "Book", "price": 20.0}], "status": "active"}
        })

        # Reset DISCOUNT_STORE state
        for code in DISCOUNT_STORE:
            DISCOUNT_STORE[code] = False

    def test_valid_checkout_no_discount(self):
        """Test successful checkout without discount code."""
        result = process_cart_checkout("cart_123", "user123")
        assert "Success" in result
        assert "Total paid: $1000.00" in result
        assert CART_STORE["cart_123"]["status"] == "completed"

    def test_valid_checkout_with_discount(self):
        """Test successful checkout with valid discount code WELCOME50."""
        result = process_cart_checkout("cart_123", "user123", "WELCOME50")
        assert "Success" in result
        assert "Total paid: $500.00" in result
        assert CART_STORE["cart_123"]["status"] == "completed"
        assert DISCOUNT_STORE["WELCOME50"] is True

    def test_valid_checkout_with_discount_summer20(self):
        """Test successful checkout with valid discount code SUMMER20."""
        result = process_cart_checkout("cart_456", "user456", "SUMMER20")
        assert "Success" in result
        assert "Total paid: $80.00" in result
        assert CART_STORE["cart_456"]["status"] == "completed"
        assert DISCOUNT_STORE["SUMMER20"] is True

    def test_invalid_cart_id(self):
        """Test that invalid cart ID returns error."""
        result = process_cart_checkout("invalid_cart", "user123")
        assert "Error" in result
        assert "Cart not found" in result

    def test_unauthorized_checkout_idor(self):
        """Test that user cannot checkout another user's cart (IDOR prevention)."""
        result = process_cart_checkout("cart_123", "user456")
        assert "Error" in result
        assert "Unauthorized checkout" in result
        assert CART_STORE["cart_123"]["status"] == "active"

    def test_double_checkout_prevention(self):
        """Test that a cart cannot be checked out twice."""
        # First checkout should succeed
        result1 = process_cart_checkout("cart_123", "user123")
        assert "Success" in result1

        # Second checkout should fail
        result2 = process_cart_checkout("cart_123", "user123")
        assert "Error" in result2
        assert "already been checked out" in result2

    def test_guest_checkout_with_discount_rejection(self):
        """Test that guest checkout with a discount code is rejected."""
        result = process_cart_checkout("cart_guest", "guest_789", "WELCOME50")
        assert "Error" in result
        assert "Registered user account required" in result
        assert CART_STORE["cart_guest"]["status"] == "active"
        assert DISCOUNT_STORE["WELCOME50"] is False

    def test_guest_checkout_without_discount_success(self):
        """Test that guest checkout without a discount code is allowed."""
        result = process_cart_checkout("cart_guest", "guest_789")
        assert "Success" in result
        assert "Total paid: $20.00" in result
        assert CART_STORE["cart_guest"]["status"] == "completed"

    def test_invalid_discount_code(self):
        """Test that checkout fails if discount code is invalid."""
        result = process_cart_checkout("cart_123", "user123", "INVALID99")
        assert "Error" in result
        assert "Invalid discount code" in result
        assert CART_STORE["cart_123"]["status"] == "active"

    def test_already_redeemed_discount_code(self):
        """Test that checkout fails if discount code has already been redeemed."""
        DISCOUNT_STORE["WELCOME50"] = True
        result = process_cart_checkout("cart_123", "user123", "WELCOME50")
        assert "Error" in result
        assert "already been redeemed" in result
        assert CART_STORE["cart_123"]["status"] == "active"


class TestUpdateDiscountStatus:
    """Test suite for update_discount_status tool."""

    def setup_method(self):
        """Reset discount codes before each test."""
        for code in DISCOUNT_STORE:
            DISCOUNT_STORE[code] = False

    def test_admin_deactivate_discount(self):
        """Test that admin can successfully deactivate an active discount code."""
        result = update_discount_status("WELCOME50", False, "admin_123")
        assert "Success" in result
        assert "deactivated" in result
        assert DISCOUNT_STORE["WELCOME50"] is True  # True means redeemed/inactive

    def test_admin_activate_discount(self):
        """Test that admin can successfully activate an inactive discount code."""
        DISCOUNT_STORE["WELCOME50"] = True  # Start as inactive
        result = update_discount_status("WELCOME50", True, "admin_123")
        assert "Success" in result
        assert "activated" in result
        assert DISCOUNT_STORE["WELCOME50"] is False  # False means active/available

    def test_unauthorized_user_rejection(self):
        """Test that standard registered users are rejected."""
        result = update_discount_status("WELCOME50", False, "user123")
        assert "Error" in result
        assert "Administrator privileges required" in result
        assert DISCOUNT_STORE["WELCOME50"] is False

    def test_unauthorized_guest_rejection(self):
        """Test that guest users are rejected."""
        result = update_discount_status("WELCOME50", False, "guest_123")
        assert "Error" in result
        assert "Administrator privileges required" in result
        assert DISCOUNT_STORE["WELCOME50"] is False

    def test_missing_user_id_rejection(self):
        """Test that missing user ID is rejected."""
        result = update_discount_status("WELCOME50", False, "")
        assert "Error" in result
        assert "Administrator privileges required" in result
        assert DISCOUNT_STORE["WELCOME50"] is False

    def test_none_user_id_rejection(self):
        """Test that None user ID is rejected."""
        result = update_discount_status("WELCOME50", False, None)
        assert "Error" in result
        assert "Administrator privileges required" in result
        assert DISCOUNT_STORE["WELCOME50"] is False

    def test_invalid_discount_code(self):
        """Test that updating a non-existent discount code returns error."""
        result = update_discount_status("INVALID99", False, "admin_123")
        assert "Error" in result
        assert "Discount code not found" in result
