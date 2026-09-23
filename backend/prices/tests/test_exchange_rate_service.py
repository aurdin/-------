from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from prices.models import Currency, ExchangeRate
from prices.services import get_current_exchange_rate


class GetCurrentExchangeRateTests(TestCase):
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

        cls.base_time = timezone.datetime(
            2026,
            9,
            23,
            10,
            0,
            tzinfo=timezone.get_current_timezone(),
        )

    def test_returns_latest_rate_at_requested_time(self):
        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.base_time,
        )

        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.30"),
            valid_from=self.base_time + timezone.timedelta(hours=2),
        )

        result = get_current_exchange_rate(
            base_currency=self.uah,
            quote_currency=self.usd,
            at=self.base_time + timezone.timedelta(hours=1),
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.rate, Decimal("41.25"))

    def test_returns_latest_rate_when_multiple_rates_are_available(self):
        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.base_time,
        )

        latest = ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.30"),
            valid_from=self.base_time + timezone.timedelta(hours=2),
        )

        result = get_current_exchange_rate(
            base_currency=self.uah,
            quote_currency=self.usd,
            at=self.base_time + timezone.timedelta(hours=3),
        )

        self.assertEqual(result, latest)

    def test_does_not_return_future_rate(self):
        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.30"),
            valid_from=self.base_time + timezone.timedelta(hours=1),
        )

        result = get_current_exchange_rate(
            base_currency=self.uah,
            quote_currency=self.usd,
            at=self.base_time,
        )

        self.assertIsNone(result)

    def test_does_not_return_rate_for_another_currency_pair(self):
        eur = Currency.objects.create(
            code="EUR",
            name="Euro",
            symbol="€",
        )

        ExchangeRate.objects.create(
            base_currency=self.uah,
            quote_currency=self.usd,
            rate=Decimal("41.25"),
            valid_from=self.base_time,
        )

        result = get_current_exchange_rate(
            base_currency=self.uah,
            quote_currency=eur,
            at=self.base_time + timezone.timedelta(hours=1),
        )

        self.assertIsNone(result)
