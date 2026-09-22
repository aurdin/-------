from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Group,
    Product,
    Type,
)
from prices.models import Discount
class DiscountModelTests(TestCase):
    def create_product(self, article="DISCOUNT-001"):
        category = Category.objects.create(
            name="Discount Category",
        )
        group = Group.objects.create(
            name="Discount Group",
        )
        brand = Brand.objects.create(
            name="Discount Brand",
        )
        product_type = Type.objects.create(
            name="Discount Type",
        )

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

    def valid_to(self):
        return datetime(
            2026,
            2,
            1,
            tzinfo=dt_timezone.utc,
        )

    def test_percent_discount_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        discount.full_clean()

        self.assertEqual(
            discount.value,
            Decimal(10),
        )

    def test_fixed_discount_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_FIXED,
            value=Decimal("10.50"),
            valid_from=self.valid_from(),
        )

        discount.full_clean()

        self.assertEqual(
            discount.value,
            Decimal("10.50"),
        )

    def test_zero_discount_rejected(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(0),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_negative_discount_rejected(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(-10),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_percent_discount_over_100_rejected(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("100.01"),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_unknown_discount_type_rejected(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type="unknown",
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_discount_without_dates_is_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
        )

        discount.full_clean()

        self.assertIsNone(discount.valid_from)
        self.assertIsNone(discount.valid_to)    

    def test_open_ended_discount_is_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        discount.full_clean()

        self.assertIsNone(discount.valid_to)

    def test_valid_discount_period_is_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
            valid_to=self.valid_to(),
        )

        discount.full_clean()

        self.assertGreater(
            discount.valid_to,
            discount.valid_from,
        )

    def test_equal_validity_dates_are_rejected(self):
        product = self.create_product()

        date = self.valid_from()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=date,
            valid_to=date,
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_valid_to_before_valid_from_is_rejected(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_to(),
            valid_to=self.valid_from(),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_discount_is_active_by_default(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        discount.full_clean()

        self.assertTrue(discount.is_active)

    def test_discount_string_representation(self):
        product = self.create_product()

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        self.assertEqual(
            str(discount),
            f"{product} — 10 (percent)",
        )

    def test_discount_protects_product_from_deletion(self):
        product = self.create_product()

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ProtectedError):
            product.delete()

        self.assertTrue(
            Discount.objects.filter(id=discount.id).exists() 
        )
    def test_discount_with_only_valid_to_is_allowed(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
            valid_to=self.valid_to(),
        )

        discount.full_clean()

        self.assertIsNone(discount.valid_from)
        self.assertEqual(
            discount.valid_to,
            self.valid_to(),
        )        