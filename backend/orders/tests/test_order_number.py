from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase

from orders.services import generate_order_number
from orders.models import OrderNumberSequence


class OrderNumberServiceTests(TestCase):
    @patch("orders.services.timezone.now")
    def test_generates_first_order_number(self, mock_now):
        mock_now.return_value = datetime(2026, 9, 25, 14, 30, 0, tzinfo=timezone.utc)

        number = generate_order_number()

        self.assertEqual(number, "SMEL-20260925-000001")

    @patch("orders.services.timezone.now")
    def test_sequence_is_global(self, mock_now):
        mock_now.return_value = datetime(2026, 9, 25, 14, 30, 0, tzinfo=timezone.utc)

        first = generate_order_number()
        second = generate_order_number()

        self.assertEqual(first, "SMEL-20260925-000001")
        self.assertEqual(second, "SMEL-20260925-000002")

    @patch("orders.services.timezone.now")
    def test_sequence_does_not_reset_on_new_day(self, mock_now):
        mock_now.return_value = datetime(2026, 9, 25, 23, 59, 0, tzinfo=timezone.utc)
        first = generate_order_number()

        mock_now.return_value = datetime(2026, 9, 26, 0, 1, 0, tzinfo=timezone.utc)
        second = generate_order_number()

        self.assertEqual(first, "SMEL-20260925-000001")
        self.assertEqual(second, "SMEL-20260926-000002")
    
    @patch("orders.services.timezone.now")
    def test_sequence_exceeds_six_digits(self, mock_now):
        mock_now.return_value = datetime(
            2026, 9, 25, 14, 30, 0, tzinfo=timezone.utc
        )

        OrderNumberSequence.objects.create(
            pk=1,
            value=999999,
        )

        number = generate_order_number()

        self.assertEqual(number, "SMEL-20260925-1000000")
