from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Group,
    Product,
    Type,
)
from prices.models import Discount
from prices.services import (
    create_discount,
    update_discount,
)

class DiscountUpdateServiceTests(TestCase):
    def create_product(self, article="UPDATE-001"):
        category = Category.objects.create(name="Update Category")
        group = Group.objects.create(name="Update Group")
        brand = Brand.objects.create(name="Update Brand")
        product_type = Type.objects.create(name="Update Type")

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

    def test_discount_can_be_updated(self):
        product = self.create_product()

        discount = self.create_discount(
            product,
            self.valid_from(),
            self.date_15(),
            value="10.00",
        )

        update_discount(
            discount,
            value=Decimal("15.00"),
        )

        discount.refresh_from_db()

        self.assertEqual(discount.value, Decimal("15.00"))

    def test_discount_period_can_be_updated(self):
        product = self.create_product()

        discount = self.create_discount(
            product,
            self.valid_from(),
            self.date_15(),
        )

        update_discount(
            discount,
            valid_to=self.date_31(),
        )

        discount.refresh_from_db()

        self.assertEqual(discount.valid_to, self.date_31())

    def test_discount_can_be_changed_to_open_ended(self):
        product = self.create_product()

        discount = self.create_discount(
            product,
            self.valid_from(),
            self.date_15(),
        )

        update_discount(
            discount,
            valid_to=None,
        )

        discount.refresh_from_db()

        self.assertIsNone(discount.valid_to)

    def test_discount_can_be_deactivated(self):
        product = self.create_product()

        discount = self.create_discount(
            product,
            self.valid_from(),
        )

        update_discount(
            discount,
            is_active=False,
        )

        discount.refresh_from_db()

        self.assertFalse(discount.is_active)

    def test_update_rejects_overlapping_period(self):
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

        with self.assertRaises(ValidationError):
            update_discount(
                second,
                valid_from=self.valid_from(),
                valid_to=self.date_31(),
            )

        second.refresh_from_db()

        self.assertEqual(
            second.valid_from,
            self.date_15(),
        )

        self.assertEqual(
            second.valid_to,
            self.date_31(),
        )

    def test_update_can_resolve_existing_overlap(self):
        product = self.create_product()

        self.create_discount(
            product,
            self.valid_from(),
            self.date_15(),
        )

        second = self.create_discount(
            product,
            self.date_31(),
            self.date_10_feb(),
        )

        update_discount(
            second,
            valid_from=self.date_15(),
        )

        second.refresh_from_db()

        self.assertEqual(
            second.valid_from,
            self.date_15(),
        )

    def test_update_keeps_other_fields_unchanged(self):
        product = self.create_product()

        discount = self.create_discount(
            product,
            self.valid_from(),
            self.date_31(),
            value="10.00",
        )

        update_discount(
            discount,
            value=Decimal("20.00"),
        )

        discount.refresh_from_db()

        self.assertEqual(discount.type, Discount.DISCOUNT_TYPE_PERCENT)
        self.assertEqual(discount.value, Decimal("20.00"))
        self.assertEqual(discount.valid_from, self.valid_from())
        self.assertEqual(discount.valid_to, self.date_31())
        self.assertTrue(discount.is_active)