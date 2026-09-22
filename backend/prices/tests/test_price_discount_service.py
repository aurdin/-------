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
from prices.models import (
    Currency,
    Discount,
    Price,
)
from prices.services import (
    calculate_final_price,
    get_current_discount,
    get_current_price,
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