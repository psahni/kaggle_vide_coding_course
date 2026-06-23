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
Tests discount code redemption and product catalog functionality.
"""

import pytest
from app.agent import redeem_discount_code, get_available_products, DISCOUNT_CODES


class TestDiscountCodeRedemption:
    """Test suite for discount code redemption tool."""

    def setup_method(self):
        """Reset discount codes before each test."""
        for code in DISCOUNT_CODES:
            DISCOUNT_CODES[code][1].clear()

    def test_valid_code_redemption(self):
        """Test successful redemption of a valid discount code."""
        result = redeem_discount_code("WELCOME50", "user123")
        assert "Success" in result
        assert "user123" in result
        assert "WELCOME50" in result
        assert "50%" in result

    def test_case_insensitive_code(self):
        """Test that discount codes are case-insensitive."""
        result1 = redeem_discount_code("welcome50", "user123")
        result2 = redeem_discount_code("WELCOME50", "user456")
        assert "Success" in result1
        assert "Success" in result2

    def test_code_with_whitespace(self):
        """Test that codes are stripped of whitespace."""
        result = redeem_discount_code("  SUMMER20  ", "user123")
        assert "Success" in result
        assert "20%" in result

    def test_invalid_code(self):
        """Test that invalid codes are rejected."""
        result = redeem_discount_code("INVALID99", "user123")
        assert "Error" in result
        assert "Invalid discount code" in result

    def test_duplicate_redemption_prevention(self):
        """Test that the same user cannot redeem a code twice."""
        user_id = "user123"

        # First redemption should succeed
        result1 = redeem_discount_code("SAVE30", user_id)
        assert "Success" in result1

        # Second redemption should fail
        result2 = redeem_discount_code("SAVE30", user_id)
        assert "Error" in result2
        assert "already redeemed" in result2

    def test_different_users_can_redeem_same_code(self):
        """Test that different users can redeem the same code."""
        result1 = redeem_discount_code("WELCOME50", "user1")
        result2 = redeem_discount_code("WELCOME50", "user2")
        assert "Success" in result1
        assert "Success" in result2

    def test_missing_user_id(self):
        """Test that missing user ID is rejected."""
        result = redeem_discount_code("WELCOME50", "")
        assert "Error" in result
        assert "User ID is required" in result

    def test_none_user_id(self):
        """Test that None user ID is handled."""
        result = redeem_discount_code("WELCOME50", None)
        assert "Error" in result

    def test_all_discount_codes_available(self):
        """Test that all expected discount codes are available."""
        expected_codes = {"WELCOME50", "SUMMER20", "SAVE30"}
        actual_codes = set(DISCOUNT_CODES.keys())
        assert expected_codes == actual_codes


class TestProductCatalog:
    """Test suite for product catalog tool."""

    def test_get_available_products_returns_string(self):
        """Test that product catalog returns a string."""
        result = get_available_products()
        assert isinstance(result, str)

    def test_product_catalog_contains_categories(self):
        """Test that product catalog includes all expected categories."""
        result = get_available_products()
        assert "Electronics" in result
        assert "Clothing" in result
        assert "Home & Garden" in result

    def test_product_catalog_contains_products(self):
        """Test that product catalog includes expected products."""
        result = get_available_products()
        assert "Laptop" in result
        assert "T-Shirt" in result
        assert "Coffee Maker" in result

    def test_product_catalog_contains_prices(self):
        """Test that product catalog includes prices."""
        result = get_available_products()
        assert "$" in result
        assert "999" in result or "99" in result

    def test_product_catalog_non_empty(self):
        """Test that product catalog is not empty."""
        result = get_available_products()
        assert len(result) > 0
        assert result.startswith("Available Products")
