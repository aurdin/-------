from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Group, Product, Type
from prices.models import Currency, Discount, Price, ExchangeRate
from prices.services import get_calculated_price_in_currency


class GetCalculatedPriceInCurrencyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Test category",
        )

        cls.group = Group.objects.create(
            name="Test group",
        )

        cls.product_type = Type.objects.create(
            name="Test type",
        )

        cls.product = Product.objects.create(
            article="TEST-CURRENCY-001",
            category=cls.category,
            group=cls.group,
            type=cls.product_type,
            sales_unit="pcs",
        )

        cls.uah = Currency.objects.create(
            code="UAH",
            name="Ukrainian Hryvnia",
            symbol="₴",
        )

        cls.usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        cls.at = timezone.datetime(
            2026,
            9,
            23,
            10,
            0,
            tzinfo=timezone.get_current_timezone(),
        )    

    def test_uah_price_is_calculated_without_exchange_rate(self):
        Price.objects.create(
            product=self.product,
            currency=self.uah,
            amount=Decimal("4125.00"),
            valid_from=self.at,
        )

        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.uah,
            at=self.at,
        )

        self.assertEqual(
            result["final_price"],
            Decimal("4125.00"),
        )

    def test_foreign_currency_price_is_converted_from_uah(self):
        Price.objects.create(
            product=self.product,
            currency=self.uah,
            amount=Decimal("4125.00"),
            valid_from=self.at,
        )

        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.at,
        )

        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.usd,
            at=self.at,
        )

        self.assertEqual(
            result["final_price"],
            Decimal("100.00"),
        )

    def test_discount_is_applied_before_currency_conversion(self):
        Price.objects.create(
            product=self.product,
            currency=self.uah,
            amount=Decimal("4125.00"),
            valid_from=self.at,
        )

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=self.at,
            is_active=True,
        )

        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.at,
        )

        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.usd,
            at=self.at,
        )

        self.assertEqual(
            result["final_price"],
            Decimal("90.00"),
        )

    def test_returns_none_when_uah_price_does_not_exist(self):
        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.usd,
            at=self.at,
        )

        self.assertIsNone(result)

    def test_returns_none_when_exchange_rate_does_not_exist(self):
        Price.objects.create(
            product=self.product,
            currency=self.uah,
            amount=Decimal("4125.00"),
            valid_from=self.at,
        )

        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.usd,
            at=self.at,
        )

        self.assertIsNone(result)

    def test_future_exchange_rate_is_not_used(self):
        Price.objects.create(
            product=self.product,
            currency=self.uah,
            amount=Decimal("4125.00"),
            valid_from=self.at,
        )

        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.at + timezone.timedelta(hours=1),
        )

        result = get_calculated_price_in_currency(
            product=self.product,
            currency=self.usd,
            at=self.at,
        )

        self.assertIsNone(result)
