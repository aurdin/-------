from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from prices.models import Currency, ExchangeRate


class ExchangeRateModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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

        cls.valid_from = timezone.datetime(
            2026,
            9,
            23,
            10,
            0,
            tzinfo=timezone.get_current_timezone(),
        )

    def test_create_exchange_rate(self):
        exchange_rate = ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25000000"),
            valid_from=self.valid_from,
        )

        self.assertEqual(exchange_rate.base_currency, self.uah)
        self.assertEqual(exchange_rate.quote_currency, self.usd)
        self.assertEqual(exchange_rate.rate, Decimal("41.25000000"))
        self.assertEqual(exchange_rate.valid_from, self.valid_from)

    def test_rate_must_be_positive(self):
        exchange_rate = ExchangeRate(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal(0),
            valid_from=self.valid_from,
        )

        with self.assertRaises(ValidationError):
            exchange_rate.full_clean()

    def test_negative_rate_is_invalid(self):
        exchange_rate = ExchangeRate(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("-1"),  # noqa: FURB157
            valid_from=self.valid_from,
        )

        with self.assertRaises(ValidationError):
            exchange_rate.full_clean()

    def test_base_and_quote_currency_must_be_different(self):
        exchange_rate = ExchangeRate(
            base_currency=self.uah,
            quote_currency=self.uah,
            rate=Decimal(1),
            valid_from=self.valid_from,
        )

        with self.assertRaises(ValidationError):
            exchange_rate.full_clean()

    def test_same_currency_pair_and_same_valid_from_are_unique(self):
        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.valid_from,
        )

        with self.assertRaises(IntegrityError):
            ExchangeRate.objects.create(
                base_currency=self.uah,
                quote_currency=self.usd,
                rate=Decimal("41.30"),
                valid_from=self.valid_from,
            )

    def test_same_currency_pair_with_different_valid_from_is_allowed(self):
        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.valid_from,
        )

        later = self.valid_from + timezone.timedelta(hours=1)

        exchange_rate = ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.30"),
            valid_from=later,
        )

        self.assertEqual(exchange_rate.rate, Decimal("41.30"))

    def test_string_representation(self):
        exchange_rate = ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.valid_from,
        )

        self.assertEqual(
            str(exchange_rate),
            "UAH → USD: 41.25",
        )
