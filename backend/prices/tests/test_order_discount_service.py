from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from prices.models import OrderDiscount
from prices.services import (
    calculate_order_discount,
    get_current_order_discount,
)


class OrderDiscountServiceTests(TestCase):
    def date_1_jan(self):
        return datetime(2026, 1, 1, tzinfo=dt_timezone.utc)

    def date_15_jan(self):
        return datetime(2026, 1, 15, tzinfo=dt_timezone.utc)

    def date_1_feb(self):
        return datetime(2026, 2, 1, tzinfo=dt_timezone.utc)

    def create_discount(
        self,
        *,
        name="Test order discount",
        discount_type=OrderDiscount.DISCOUNT_TYPE_PERCENT,
        value="5.00",
        min_order_amount="5000.00",
        max_order_amount="6000.00",
        valid_from=None,
        valid_to=None,
        is_active=True,
    ):
        return OrderDiscount.objects.create(
            name=name,
            type=discount_type,
            value=Decimal(value),
            min_order_amount=Decimal(min_order_amount),
            max_order_amount=(
                Decimal(max_order_amount) if max_order_amount is not None else None
            ),
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
        )

    def test_returns_matching_discount_for_amount_range(self):
        discount = self.create_discount()

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_15_jan(),
        )

        self.assertEqual(result, discount)

    def test_amount_below_minimum_returns_none(self):
        self.create_discount()

        result = get_current_order_discount(
            Decimal("4999.99"),
            self.date_15_jan(),
        )

        self.assertIsNone(result)

    def test_maximum_boundary_is_exclusive(self):
        first = self.create_discount(
            name="5 percent",
            value="5.00",
            min_order_amount="5000.00",
            max_order_amount="6000.00",
        )

        second = self.create_discount(
            name="7 percent",
            value="7.00",
            min_order_amount="6000.00",
            max_order_amount="8000.00",
        )

        result = get_current_order_discount(
            Decimal("6000.00"),
            self.date_15_jan(),
        )

        self.assertEqual(result, second)
        self.assertNotEqual(result, first)

    def test_unlimited_maximum_matches_amount_above_minimum(self):
        discount = self.create_discount(
            min_order_amount="8000.00",
            max_order_amount=None,
            value="10.00",
        )

        result = get_current_order_discount(
            Decimal("15000.00"),
            self.date_15_jan(),
        )

        self.assertEqual(result, discount)

    def test_inactive_discount_is_ignored(self):
        self.create_discount(
            is_active=False,
        )

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_15_jan(),
        )

        self.assertIsNone(result)

    def test_discount_before_valid_from_is_ignored(self):
        self.create_discount(
            valid_from=self.date_1_feb(),
        )

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_15_jan(),
        )

        self.assertIsNone(result)

    def test_discount_at_valid_from_is_active(self):
        discount = self.create_discount(
            valid_from=self.date_1_jan(),
        )

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_1_jan(),
        )

        self.assertEqual(result, discount)

    def test_discount_at_valid_to_is_inactive(self):
        self.create_discount(
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_1_feb(),
        )

        self.assertIsNone(result)

    def test_discount_without_dates_is_always_active(self):
        discount = self.create_discount()

        result = get_current_order_discount(
            Decimal("5500.00"),
            self.date_15_jan(),
        )

        self.assertEqual(result, discount)

    def test_fixed_discount_is_calculated(self):
        discount = self.create_discount(
            discount_type=OrderDiscount.DISCOUNT_TYPE_FIXED,
            value="250.00",
        )

        result = calculate_order_discount(
            Decimal("5500.00"),
            discount,
        )

        self.assertEqual(result, Decimal("250.00"))

    def test_percent_discount_is_calculated(self):
        discount = self.create_discount(
            value="5.00",
        )

        result = calculate_order_discount(
            Decimal("5500.00"),
            discount,
        )

        self.assertEqual(result, Decimal("275.00"))

    def test_percent_discount_is_calculated_with_two_decimal_places(self):
        discount = self.create_discount(
            value="7.00",
        )

        result = calculate_order_discount(
            Decimal("5999.99"),
            discount,
        )

        self.assertEqual(result, Decimal("419.9993").quantize(Decimal("0.01")))

    def test_discount_cannot_exceed_subtotal(self):
        discount = self.create_discount(
            discount_type=OrderDiscount.DISCOUNT_TYPE_FIXED,
            value="6000.00",
        )

        result = calculate_order_discount(
            Decimal("5500.00"),
            discount,
        )

        self.assertEqual(result, Decimal("5500.00"))

    def test_none_discount_returns_zero(self):
        result = calculate_order_discount(
            Decimal("5500.00"),
            None,
        )

        self.assertEqual(result, Decimal("0.00"))

    def test_negative_subtotal_is_rejected(self):
        with self.assertRaises(ValidationError):
            calculate_order_discount(
                Decimal("-1.00"),
                None,
            )

    def test_zero_subtotal_is_allowed_and_returns_zero(self):
        result = calculate_order_discount(
            Decimal("0.00"),
            None,
        )

        self.assertEqual(result, Decimal("0.00"))
