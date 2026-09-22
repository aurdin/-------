from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from prices.models import OrderDiscount
from prices.services import (
    create_order_discount,
    update_order_discount,
)


class OrderDiscountUpdateServiceTests(TestCase):
    def date_1_jan(self):
        return datetime(
            2026,
            1,
            1,
            tzinfo=dt_timezone.utc,
        )

    def date_15_jan(self):
        return datetime(
            2026,
            1,
            15,
            tzinfo=dt_timezone.utc,
        )

    def date_1_feb(self):
        return datetime(
            2026,
            2,
            1,
            tzinfo=dt_timezone.utc,
        )

    def date_15_feb(self):
        return datetime(
            2026,
            2,
            15,
            tzinfo=dt_timezone.utc,
        )

    def create_discount(
        self,
        *,
        name="Test discount",
        min_order_amount="5000.00",
        max_order_amount="8000.00",
        valid_from=None,
        valid_to=None,
        is_active=True,
    ):
        return create_order_discount(
            name=name,
            discount_type=OrderDiscount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("5.00"),
            min_order_amount=Decimal(min_order_amount),
            max_order_amount=(
                Decimal(max_order_amount) if max_order_amount is not None else None
            ),
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
        )

    def test_update_name(self):
        discount = self.create_discount()

        updated = update_order_discount(
            discount,
            name="Updated discount",
        )

        self.assertEqual(
            updated.name,
            "Updated discount",
        )

    def test_update_value(self):
        discount = self.create_discount()

        updated = update_order_discount(
            discount,
            value=Decimal("7.00"),
        )

        self.assertEqual(
            updated.value,
            Decimal("7.00"),
        )

    def test_update_amount_range(self):
        discount = self.create_discount()

        updated = update_order_discount(
            discount,
            min_order_amount=Decimal("6000.00"),
            max_order_amount=Decimal("9000.00"),
        )

        self.assertEqual(
            updated.min_order_amount,
            Decimal("6000.00"),
        )
        self.assertEqual(
            updated.max_order_amount,
            Decimal("9000.00"),
        )

    def test_update_period(self):
        discount = self.create_discount()

        updated = update_order_discount(
            discount,
            valid_from=self.date_1_feb(),
            valid_to=self.date_15_feb(),
        )

        self.assertEqual(
            updated.valid_from,
            self.date_1_feb(),
        )
        self.assertEqual(
            updated.valid_to,
            self.date_15_feb(),
        )

    def test_update_can_clear_open_ended_max_amount(self):
        discount = self.create_discount()

        updated = update_order_discount(
            discount,
            max_order_amount=None,
        )

        self.assertIsNone(
            updated.max_order_amount,
        )

    def test_update_can_clear_valid_from(self):
        discount = self.create_discount(
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        updated = update_order_discount(
            discount,
            valid_from=None,
        )

        self.assertIsNone(
            updated.valid_from,
        )

    def test_update_can_clear_valid_to(self):
        discount = self.create_discount(
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        updated = update_order_discount(
            discount,
            valid_to=None,
        )

        self.assertIsNone(
            updated.valid_to,
        )

    def test_update_rejects_amount_range_conflict(self):
        self.create_discount(
            name="Existing",
            min_order_amount="5000.00",
            max_order_amount="8000.00",
        )

        discount = self.create_discount(
            name="Updated",
            min_order_amount="8000.00",
            max_order_amount="10000.00",
        )

        with self.assertRaises(ValidationError):
            update_order_discount(
                discount,
                min_order_amount=Decimal("7000.00"),
            )

    def test_update_rejects_period_conflict(self):
        self.create_discount(
            name="Existing",
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        discount = self.create_discount(
            name="Updated",
            valid_from=self.date_1_feb(),
            valid_to=self.date_15_feb(),
        )

        with self.assertRaises(ValidationError):
            update_order_discount(
                discount,
                valid_from=self.date_15_jan(),
            )

    def test_update_allows_adjacent_amount_range(self):
        self.create_discount(
            name="Existing",
            min_order_amount="5000.00",
            max_order_amount="8000.00",
        )

        discount = self.create_discount(
            name="Updated",
            min_order_amount="8000.00",
            max_order_amount="10000.00",
        )

        updated = update_order_discount(
            discount,
            min_order_amount=Decimal("8000.00"),
        )

        self.assertEqual(
            updated.min_order_amount,
            Decimal("8000.00"),
        )

    def test_update_allows_non_overlapping_period(self):
        self.create_discount(
            name="Existing",
            valid_from=self.date_1_jan(),
            valid_to=self.date_1_feb(),
        )

        discount = self.create_discount(
            name="Updated",
            valid_from=self.date_1_feb(),
            valid_to=self.date_15_feb(),
        )

        updated = update_order_discount(
            discount,
            valid_from=self.date_1_feb(),
        )

        self.assertEqual(
            updated.valid_from,
            self.date_1_feb(),
        )

    def test_update_inactive_discount_does_not_check_conflict(self):
        self.create_discount(
            name="Existing",
            min_order_amount="5000.00",
            max_order_amount="8000.00",
        )

        discount = self.create_discount(
            name="Inactive",
            min_order_amount="8000.00",
            max_order_amount="10000.00",
            is_active=False,
        )

        updated = update_order_discount(
            discount,
            min_order_amount=Decimal("6000.00"),
        )

        self.assertEqual(
            updated.min_order_amount,
            Decimal("6000.00"),
        )
        self.assertFalse(updated.is_active)
