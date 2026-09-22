from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import IntegrityError
from prices.models import Currency

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