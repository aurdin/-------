from decimal import Decimal

from django.test import TestCase

from prices.services import convert_amount


class ConvertAmountTests(TestCase):
    def test_converts_uah_to_foreign_currency(self):
        result = convert_amount(
            amount=Decimal("4125.00"),
            rate=Decimal("41.25"),
        )

        self.assertEqual(result, Decimal("100.00"))

    def test_converts_with_fractional_result(self):
        result = convert_amount(
            amount=Decimal("1000.00"),
            rate=Decimal("41.25"),
        )

        self.assertEqual(result, Decimal("24.24"))

    def test_result_is_rounded_to_two_decimal_places(self):
        result = convert_amount(
            amount=Decimal("100.00"),
            rate=Decimal("41.27"),
        )

        self.assertEqual(result, Decimal("2.42"))

    def test_zero_amount_returns_zero(self):
        result = convert_amount(
            amount=Decimal("0.00"),
            rate=Decimal("41.25"),
        )

        self.assertEqual(result, Decimal("0.00"))

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            convert_amount(
                amount=Decimal("-100.00"),
                rate=Decimal("41.25"),
            )

    def test_zero_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            convert_amount(
                amount=Decimal("100.00"),
                rate=Decimal(0),
            )

    def test_negative_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            convert_amount(
                amount=Decimal("100.00"),
                rate=Decimal("-1"),  # noqa: FURB157
            )
