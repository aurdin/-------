from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

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
    Discount,
)
from prices.services import (
    calculate_final_price,
    create_discount,
    get_current_discount,
    get_current_price,
    update_discount,
)
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError


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

        self.assertTrue(
            Price.objects.filter(id=price.id).exists()
        )

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

        self.assertTrue(
            Currency.objects.filter(id=currency.id).exists()
        )
        self.assertTrue(
            Price.objects.filter(id=price.id).exists()
        )        

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

    def test_valid_from_is_required(self):
        product = self.create_product()

        discount = Discount(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal(10),
        )

        with self.assertRaises(ValidationError):
            discount.full_clean()

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


class CurrencyModelTests(TestCase):

    def test_currency_creation(self):
        currency = Currency.objects.create(
            code="UAH",
            name="Ukrainian Hryvnia",
            symbol="₴",
        )

        self.assertEqual(currency.code, "UAH")
        self.assertEqual(currency.name, "Ukrainian Hryvnia")
        self.assertEqual(currency.symbol, "₴")
        self.assertTrue(currency.is_active)

    def test_currency_code_is_unique(self):
        Currency.objects.create(
            code="UAH",
            name="Ukrainian Hryvnia",
        )

        with self.assertRaises(IntegrityError):
            Currency.objects.create(
                code="UAH",
                name="Duplicate Hryvnia",
            )

    def test_currency_name_is_required(self):
        currency = Currency(
            code="UAH",
        )

        with self.assertRaises(ValidationError):
            currency.full_clean()

    def test_currency_code_is_required(self):
        currency = Currency(
            name="Ukrainian Hryvnia",
        )

        with self.assertRaises(ValidationError):
            currency.full_clean()

    def test_currency_symbol_is_optional(self):
        currency = Currency.objects.create(
            code="EUR",
            name="Euro",
        )

        self.assertEqual(currency.symbol, "")

    def test_currency_can_be_deactivated(self):
        currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
        )

        currency.is_active = False
        currency.save()

        currency.refresh_from_db()

        self.assertFalse(currency.is_active)

    def test_currency_code_longer_than_three_characters_rejected(self):
        currency = Currency(
            code="USDX",
            name="Invalid Currency",
        )

        with self.assertRaises(ValidationError):
            currency.full_clean()

    def test_currency_string_representation(self):
        currency = Currency.objects.create(
            code="EUR",
            name="Euro",
        )

        self.assertEqual(
            str(currency),
            "EUR — Euro",
        )

class PriceDiscountServiceTests(TestCase):
    def create_product(self, article="SERVICE-001"):
        category = Category.objects.create(name="Service Category")
        group = Group.objects.create(name="Service Group")
        brand = Brand.objects.create(name="Service Brand")
        product_type = Type.objects.create(name="Service Type")

        return Product.objects.create(
            article=article,
            category=category,
            group=group,
            brand=brand,
            type=product_type,
            sales_unit="pcs",
        )

    def create_currency(self, code="UAH"):
        return Currency.objects.create(
            code=code,
            name="Ukrainian Hryvnia",
            symbol="₴",
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

    def test_current_price_is_found(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        result = get_current_price(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertEqual(result, price)

    def test_current_price_is_found_by_currency(self):
        product = self.create_product()
        uah = self.create_currency(code="UAH")
        usd = self.create_currency(code="USD")

        uah_price = Price.objects.create(
            product=product,
            currency=uah,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        Price.objects.create(
            product=product,
            currency=usd,
            amount=Decimal("25.00"),
            valid_from=self.valid_from(),
        )

        result = get_current_price(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
            currency=uah,
        )

        self.assertEqual(result, uah_price)

    def test_current_price_with_unknown_currency_is_not_found(self):
        product = self.create_product()
        uah = self.create_currency(code="UAH")
        usd = self.create_currency(code="USD")

        Price.objects.create(
            product=product,
            currency=uah,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        result = get_current_price(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
            currency=usd,
        )

        self.assertIsNone(result)    

    
    def test_future_price_is_not_current(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1200.00"),
            valid_from=self.valid_to(),
        )

        result = get_current_price(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertIsNone(result)

    def test_expired_price_is_not_current(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("900.00"),
            valid_from=datetime(
                2025,
                12,
                1,
                tzinfo=dt_timezone.utc,
            ),
            valid_to=self.valid_from(),
        )

        result = get_current_price(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertIsNone(result)

    def test_current_discount_is_found(self):
        product = self.create_product()

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.valid_from(),
        )

        result = get_current_discount(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertEqual(result, discount)

    def test_inactive_discount_is_not_current(self):
        product = self.create_product()

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.valid_from(),
            is_active=False,
        )

        result = get_current_discount(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertIsNone(result)

    def test_future_discount_is_not_current(self):
        product = self.create_product()

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.valid_to(),
        )

        result = get_current_discount(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertIsNone(result)

    def test_expired_discount_is_not_current(self):
        product = self.create_product()

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=datetime(
                2025,
                12,
                1,
                tzinfo=dt_timezone.utc,
            ),
            valid_to=self.valid_from(),
        )

        result = get_current_discount(
            product,
            datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.assertIsNone(result)

    def test_percent_discount_is_calculated(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.valid_from(),
        )

        result = calculate_final_price(price, discount)

        self.assertEqual(result, Decimal("900.00"))

    def test_fixed_discount_is_calculated(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_FIXED,
            value=Decimal("150.00"),
            valid_from=self.valid_from(),
        )

        result = calculate_final_price(price, discount)

        self.assertEqual(result, Decimal("850.00"))

    def test_without_discount_price_is_unchanged(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        result = calculate_final_price(price)

        self.assertEqual(result, Decimal("1000.00"))
        self.assertEqual(price.amount, Decimal("1000.00"))

    def test_discount_cannot_make_price_negative(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("100.00"),
            valid_from=self.valid_from(),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_FIXED,
            value=Decimal("150.00"),
            valid_from=self.valid_from(),
        )

        result = calculate_final_price(price, discount)

        self.assertEqual(result, Decimal("0.00"))

    def test_price_amount_is_not_modified_by_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=self.valid_from(),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.valid_from(),
        )

        calculate_final_price(price, discount)

        price.refresh_from_db()

        self.assertEqual(price.amount, Decimal("1000.00"))

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

class PriceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_product(self, article="API-001"):
        category = Category.objects.create(
            name="API Category",
        )
        group = Group.objects.create(
            name="API Group",
        )
        brand = Brand.objects.create(
            name="API Brand",
        )
        product_type = Type.objects.create(
            name="API Type",
        )

        return Product.objects.create(
            article=article,
            category=category,
            group=group,
            brand=brand,
            type=product_type,
            sales_unit="pcs",
        )

    def create_currency(self, code="UAH"):
        return Currency.objects.create(
            code=code,
            name="Ukrainian Hryvnia",
            symbol="₴",
        )

    def test_current_price_by_currency(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": "UAH"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], price.id)
        self.assertEqual(
            response.data["amount"],
            "1000.00",
        )

    def test_current_price_by_currency_not_found(self):
        product = self.create_product()
        currency = self.create_currency(code="UAH")

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": "USD"},
        )

        self.assertEqual(response.status_code, 400)  
        self.assertEqual(
            response.data["detail"],
            "Валюта не найдена.",
        )

    def test_current_price_requires_currency(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Параметр currency обязателен.",
        )

    def test_current_price_product_not_found(self):
        currency = self.create_currency()

        response = self.client.get(
            "/api/prices/products/999999/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Товар не найден.",
        )

    def test_current_price_not_found(self):
        product = self.create_product()
        currency = self.create_currency()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Текущая цена не найдена.",
        )

    def test_current_price_inactive_currency(self):
        product = self.create_product()

        currency = self.create_currency()
        currency.is_active = False
        currency.save()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Валюта не найдена.",
        )                     

    def test_calculated_price_without_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product"], product.id)
        self.assertEqual(response.data["currency"], "UAH")
        self.assertEqual(response.data["price"], "1000.00")
        self.assertIsNone(response.data["discount"])
        self.assertIsNone(response.data["discount_type"])
        self.assertEqual(
            response.data["final_price"],
            "1000.00",
        )

    def test_calculated_price_with_percent_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "1000.00")
        self.assertEqual(response.data["discount"], "10.00")
        self.assertEqual(
            response.data["discount_type"],
            "percent",
        )
        self.assertEqual(
            response.data["final_price"],
            "900.00",
        )

    def test_calculated_price_with_fixed_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_FIXED,
            value=Decimal("150.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "1000.00")
        self.assertEqual(response.data["discount"], "150.00")
        self.assertEqual(
            response.data["discount_type"],
            "fixed",
        )
        self.assertEqual(
            response.data["final_price"],
            "850.00",
        )


    def test_calculated_price_requires_currency(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Параметр currency обязателен.",
        )

    def test_calculated_price_not_found(self):
        product = self.create_product()
        currency = self.create_currency()

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Текущая цена не найдена.",
        )

    def test_product_price_history(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["product"],
            product.id,
        )

        self.assertEqual(
            len(response.data["prices"]),
            1,
        )
        self.assertEqual(
            response.data["prices"][0]["id"],
            price.id,
        )
        self.assertEqual(
            response.data["prices"][0]["currency"]["code"],
            "UAH",
        )

        self.assertEqual(
            len(response.data["discounts"]),
            1,
        )
        self.assertEqual(
            response.data["discounts"][0]["id"],
            discount.id,
        )
        self.assertEqual(
            response.data["discounts"][0]["type"],
            "percent",
        )

    def test_product_price_history_empty(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["product"],
            product.id,
        )
        self.assertEqual(
            response.data["prices"],
            [],
        )
        self.assertEqual(
            response.data["discounts"],
            [],
        )

    def test_product_price_history_product_not_found(self):
        response = self.client.get(
            "/api/prices/products/999999/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Товар не найден.",
        )

