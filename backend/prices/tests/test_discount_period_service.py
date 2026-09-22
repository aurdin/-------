from datetime import datetime, timezone as dt_timezone 
from decimal import Decimal

from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Group,
    Product,
    Type,
)
from prices.models import Discount
from prices.services import create_discount
from django.core.exceptions import ValidationError

class DiscountPeriodServiceTests(TestCase):
    def create_product(self, article="PERIOD-001"):
        category = Category.objects.create(name="Period Category")
        group = Group.objects.create(name="Period Group")
        brand = Brand.objects.create(name="Period Brand")
        product_type = Type.objects.create(name="Period Type")

        return Product.objects.create(
            article=article,
            category=category,
            group=group,
            brand=brand,
            type=product_type,
            sales_unit="pcs",
        )

    def valid_from(self):
        return datetime(
            2026,
            1,
            1,
            tzinfo=dt_timezone.utc,
        )

    def date_15(self):
        return datetime(
            2026,
            1,
            15,
            tzinfo=dt_timezone.utc,
        )

    def date_31(self):
        return datetime(
            2026,
            1,
            31,
            tzinfo=dt_timezone.utc,
        )

    def date_10_feb(self):
        return datetime(
            2026,
            2,
            10,
            tzinfo=dt_timezone.utc,
        )

    def create_discount(
        self,
        product,
        valid_from,
        valid_to=None,
        value="10.00",
        is_active=True,
    ):
        return create_discount(
            product=product,
            discount_type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(value),
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
        )

    def test_overlapping_discount_is_rejected(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
            self.date_31(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                self.date_15(),
                self.date_10_feb(),
            )

    def test_nested_discount_period_is_rejected(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
            self.date_10_feb(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                self.date_15(),
                self.date_31(),
            )

    def test_open_ended_discount_conflicts_with_later_discount(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                self.date_15(),
                self.date_31(),
            )

    def test_adjacent_discount_periods_are_allowed(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
            self.date_15(),
        )

        second = self.create_discount(
            product,
            self.date_15(),
            self.date_31(),
        )

        self.assertEqual(
            second.valid_from,
            self.date_15(),
        )

    def test_inactive_discount_does_not_conflict(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
            self.date_31(),
            is_active=False,
        )

        second = self.create_discount(
            product,
            self.date_15(),
            self.date_10_feb(),
        )

        self.assertEqual(second.value, Decimal("10.00"))

    def test_discounts_for_different_products_do_not_conflict(self):
        first_product = self.create_product("PERIOD-001")
        second_product = self.create_product("PERIOD-002")

        self.create_discount(
            first_product,
            self.valid_from(),
            self.date_31(),
        )

        second = self.create_discount(
            second_product,
            self.date_15(),
            self.date_10_feb(),
        )

        self.assertEqual(second.product, second_product)

    def test_existing_discount_is_not_changed_when_new_discount_is_rejected(self):
        product = self.create_product()

        existing = self.create_discount(
            product,
            self.valid_from(),
            self.date_31(),
            value="15.00",
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                self.date_15(),
                self.date_10_feb(),
                value="20.00",
            )

        existing.refresh_from_db()

        self.assertEqual(existing.value, Decimal("15.00"))
        self.assertEqual(
            Discount.objects.filter(product=product).count(),
            1,
        )

    def test_discount_without_dates_conflicts_with_any_active_discount(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=self.valid_from(),
                valid_to=self.date_31(),
            )

    def test_discount_with_only_valid_to_conflicts_with_later_period(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=self.date_31(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=self.date_15(),
                valid_to=self.date_10_feb(),
            )

    def test_discount_with_only_valid_to_allows_adjacent_period(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=self.date_15(),
        )

        discount = self.create_discount(
            product,
            valid_from=self.date_15(),
            valid_to=self.date_31(),
        )

        self.assertEqual(discount.valid_from, self.date_15())
        self.assertEqual(discount.valid_to, self.date_31())

    def test_two_open_start_discounts_conflict(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=self.date_31(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=None,
                valid_to=self.date_10_feb(),
            )

    def test_open_end_discount_conflicts_with_open_start_discount(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=self.valid_from(),
            valid_to=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=None,
                valid_to=self.date_31(),
            )

    def test_discount_without_dates_conflicts_with_open_end_discount(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=None,
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=self.valid_from(),
                valid_to=None,
            )

    def test_discount_without_dates_conflicts_with_open_start_discount(self):
        product = self.create_product()

        self.create_discount(
            product,
            valid_from=None,
            valid_to=self.date_31(),
        )

        with self.assertRaises(ValidationError):
            self.create_discount(
                product,
                valid_from=None,
                valid_to=None,
            )