from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from prices.models import OrderDiscount


class OrderDiscountModelTests(TestCase):
    def valid_from(self):
        return datetime(2026, 1, 1, tzinfo=dt_timezone.utc)

    def valid_to(self):
        return datetime(2026, 2, 1, tzinfo=dt_timezone.utc)

    def valid_data(self):
        return {
            "name": "Order discount 5000-6000",
            "type": OrderDiscount.DISCOUNT_TYPE_PERCENT,
            "value": Decimal("5.00"),
            "min_order_amount": Decimal("5000.00"),
            "max_order_amount": Decimal("6000.00"),
            "valid_from": self.valid_from(),
            "valid_to": self.valid_to(),
        }

    def test_percent_order_discount_allowed(self):
        discount = OrderDiscount(**self.valid_data())

        discount.full_clean()

        self.assertEqual(
            discount.type,
            OrderDiscount.DISCOUNT_TYPE_PERCENT,
        )

    def test_fixed_order_discount_allowed(self):
        data = self.valid_data()
        data["type"] = OrderDiscount.DISCOUNT_TYPE_FIXED
        data["value"] = Decimal("250.00")

        discount = OrderDiscount(**data)

        discount.full_clean()

    def test_zero_value_rejected(self):
        data = self.valid_data()
        data["value"] = Decimal("0.00")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_negative_value_rejected(self):
        data = self.valid_data()
        data["value"] = Decimal("-10.00")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_percent_over_100_rejected(self):
        data = self.valid_data()
        data["value"] = Decimal("100.01")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_negative_min_order_amount_rejected(self):
        data = self.valid_data()
        data["min_order_amount"] = Decimal("-1.00")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_max_order_amount_must_be_greater_than_minimum(self):
        data = self.valid_data()
        data["max_order_amount"] = Decimal("5000.00")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_max_order_amount_before_minimum_rejected(self):
        data = self.valid_data()
        data["max_order_amount"] = Decimal("4999.99")

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_unlimited_max_order_amount_allowed(self):
        data = self.valid_data()
        data["max_order_amount"] = None

        discount = OrderDiscount(**data)

        discount.full_clean()

        self.assertIsNone(discount.max_order_amount)

    def test_without_dates_allowed(self):
        data = self.valid_data()
        data["valid_from"] = None
        data["valid_to"] = None

        discount = OrderDiscount(**data)

        discount.full_clean()

    def test_only_valid_from_allowed(self):
        data = self.valid_data()
        data["valid_to"] = None

        discount = OrderDiscount(**data)

        discount.full_clean()

    def test_only_valid_to_allowed(self):
        data = self.valid_data()
        data["valid_from"] = None

        discount = OrderDiscount(**data)

        discount.full_clean()

    def test_equal_dates_rejected(self):
        data = self.valid_data()
        data["valid_to"] = data["valid_from"]

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_valid_to_before_valid_from_rejected(self):
        data = self.valid_data()
        data["valid_to"] = datetime(
            2025,
            12,
            31,
            tzinfo=dt_timezone.utc,
        )

        discount = OrderDiscount(**data)

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_discount_is_active_by_default(self):
        data = self.valid_data()
        discount = OrderDiscount(**data)

        self.assertTrue(discount.is_active)

    def test_string_representation(self):
        discount = OrderDiscount(**self.valid_data())

        self.assertEqual(
            str(discount),
            "Order discount 5000-6000 — 5.00 (percent)",
        )
