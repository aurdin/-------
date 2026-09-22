from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from prices.models import OrderDiscount
from prices.services import create_order_discount


class OrderDiscountPeriodServiceTests(TestCase):
    def date_1_jan(self):
        return datetime(2026, 1, 1, tzinfo=dt_timezone.utc)

    def date_15_jan(self):
        return datetime(2026, 1, 15, tzinfo=dt_timezone.utc)

    def date_1_feb(self):
        return datetime(2026, 2, 1, tzinfo=dt_timezone.utc)

    def date_15_feb(self):
        return datetime(2026, 2, 15, tzinfo=dt_timezone.utc)

    def create_discount(
        self,
        *,
        name="Test order discount",
        value="5.00",
        min_order_amount="5000.00",
        max_order_amount="6000.00",
        valid_from=None,
        valid_to=None,
        is_active=True,
    ):
        return create_order_discount(
            name=name,
            discount_type=OrderDiscount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(value),
            min_order_amount=Decimal(min_order_amount),
            max_order_amount=(
                Decimal(max_order_amount) if max_order_amount is not None else None
            ),
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
        )

    def test_overlapping_amount_ranges_are_rejected(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="9000.00",
            )

    def test_nested_amount_range_is_rejected(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="10000.00",
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="8000.00",
            )

    def test_adjacent_amount_ranges_are_allowed(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="6000.00",
        )

        discount = self.create_discount(
            min_order_amount="6000.00",
            max_order_amount="8000.00",
        )

        self.assertEqual(
            discount.min_order_amount,
            Decimal("6000.00"),
        )

    def test_open_ended_amount_range_conflicts_with_later_range(self):
        self.create_discount(
            min_order_amount="8000.00",
            max_order_amount=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="9000.00",
                max_order_amount="10000.00",
            )

    def test_later_range_can_exist_before_open_ended_range(self):
        self.create_discount(
            min_order_amount="8000.00",
            max_order_amount=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="7000.00",
                max_order_amount="9000.00",
            )

    def test_different_time_periods_allow_same_amount_range(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        discount = self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=self.date_1_feb(),
            valid_to=self.date_15_feb(),
        )

        self.assertEqual(
            discount.valid_from,
            self.date_1_feb(),
        )

    def test_overlapping_amount_and_time_periods_are_rejected(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="9000.00",
                valid_from=self.date_15_jan(),
                valid_to=self.date_15_feb(),
            )

    def test_overlapping_amount_ranges_with_non_overlapping_time_periods_are_allowed(
        self,
    ):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        discount = self.create_discount(
            min_order_amount="6000.00",
            max_order_amount="9000.00",
            valid_from=self.date_1_feb(),
            valid_to=self.date_15_feb(),
        )

        self.assertEqual(
            discount.min_order_amount,
            Decimal("6000.00"),
        )

    def test_open_start_time_period_conflict_is_detected(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=None,
            valid_to=self.date_1_feb(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="9000.00",
                valid_from=self.date_15_jan(),
                valid_to=self.date_15_feb(),
            )

    def test_open_end_time_period_conflict_is_detected(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=self.date_1_feb(),
            valid_to=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="9000.00",
                valid_from=self.date_15_jan(),
                valid_to=self.date_15_feb(),
            )

    def test_open_time_periods_conflict(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            valid_from=None,
            valid_to=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                min_order_amount="6000.00",
                max_order_amount="9000.00",
                valid_from=None,
                valid_to=None,
            )

    def test_inactive_discount_does_not_conflict(self):
        self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="8000.00",
            is_active=False,
        )

        discount = self.create_discount(
            min_order_amount="6000.00",
            max_order_amount="9000.00",
        )

        self.assertTrue(discount.is_active)

    def test_different_non_overlapping_amount_ranges_are_allowed(self):
        first = self.create_discount(
            min_order_amount="5000.00",
            max_order_amount="6000.00",
        )

        second = self.create_discount(
            min_order_amount="6000.00",
            max_order_amount="8000.00",
        )

        self.assertNotEqual(first.pk, second.pk)
