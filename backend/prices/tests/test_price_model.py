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
from prices.models import (
    Price,
    Currency,
)


class PriceModelTests(TestCase):
    def create_product(self, article="TEST-001"):
        category = Category.objects.create(
            name="Test Category",
        )
        group = Group.objects.create(
            name="Test Group",
        )
        brand = Brand.objects.create(
            name="Test Brand",
        )
        product_type = Type.objects.create(
            name="Test Type",
        )

        return Product.objects.create(
            article=article,
            category=category,
            group=group,
            brand=brand,
            type=product_type,
            sales_unit="pcs",
        )

    def test_positive_price_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=self.valid_from(),
        )
        price.full_clean()

        self.assertEqual(price.amount, Decimal(10))

    def test_fractional_price_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal("10.50"),
            valid_from=self.valid_from(),
        )
        price.full_clean()

        self.assertEqual(price.amount, Decimal("10.50"))

    def test_zero_price_rejected(self):
        product = self.create_product()

        price = Price(
            product=product,
            amount=Decimal(0),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_negative_price_rejected(self):
        product = self.create_product()

        price = Price(
            product=product,
            amount=Decimal(-10),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_more_than_two_decimal_places_rejected(self):
        product = self.create_product()

        price = Price(
            product=product,
            amount=Decimal("10.999"),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_maximum_price_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal("9999999999.99"),
            valid_from=self.valid_from(),
        )
        price.full_clean()

        self.assertEqual(
            price.amount,
            Decimal("9999999999.99"),
        )

    def test_price_exceeding_max_digits_rejected(self):
        product = self.create_product()

        price = Price(
            product=product,
            amount=Decimal("10000000000.00"),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_product_is_required(self):
        price = Price(
            amount=Decimal(10),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_price_protects_product_from_deletion(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ProtectedError):
            product.delete()

        self.assertTrue(Price.objects.filter(id=price.id).exists())

    def create_currency(self, code="UAH"):
        return Currency.objects.create(
            code=code,
            name="Ukrainian Hryvnia",
            symbol="₴",
        )

    def test_price_requires_currency(self):
        product = self.create_product()

        price = Price(
            product=product,
            amount=Decimal(10),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_price_with_currency_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal("10.50"),
            valid_from=self.valid_from(),
        )
        price.full_clean()

        self.assertEqual(price.currency, currency)

    def test_price_string_contains_currency_code(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("10.50"),
            valid_from=self.valid_from(),
        )

        self.assertEqual(
            str(price),
            f"{product} — 10.50 UAH",
        )

    def test_currency_protected_from_deletion_when_used_by_price(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("10.50"),
            valid_from=self.valid_from(),
        )

        with self.assertRaises(ProtectedError):
            currency.delete()

        self.assertTrue(Currency.objects.filter(id=currency.id).exists())
        self.assertTrue(Price.objects.filter(id=price.id).exists())

    def valid_from(self):
        return datetime(
            2026,
            1,
            1,
            tzinfo=dt_timezone.utc,
        )

    def test_valid_from_is_required(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_open_ended_price_is_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=self.valid_from(),
        )

        price.full_clean()

        self.assertIsNone(price.valid_to)

    def test_valid_price_period_is_allowed(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=self.valid_from(),
            valid_to=datetime(
                2026,
                2,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        price.full_clean()

        self.assertGreater(
            price.valid_to,
            price.valid_from,
        )

    def test_equal_validity_dates_are_rejected(self):
        product = self.create_product()
        currency = self.create_currency()

        date = self.valid_from()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=date,
            valid_to=date,
        )

        with self.assertRaises(ValidationError):
            price.full_clean()

    def test_valid_to_before_valid_from_is_rejected(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price(
            product=product,
            currency=currency,
            amount=Decimal(10),
            valid_from=datetime(
                2026,
                2,
                1,
                tzinfo=dt_timezone.utc,
            ),
            valid_to=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        with self.assertRaises(ValidationError):
            price.full_clean()
