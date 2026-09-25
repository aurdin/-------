from django.db import IntegrityError
from django.test import TestCase

from orders.models import OrderNumberSequence


class OrderNumberSequenceTests(TestCase):
    def test_first_sequence_value_is_zero(self):
        sequence = OrderNumberSequence.objects.create()
        self.assertEqual(sequence.value, 0)

    def test_sequence_can_increment(self):
        sequence = OrderNumberSequence.objects.create()
        sequence.value += 1
        sequence.save(update_fields=("value",))
        sequence.refresh_from_db()
        self.assertEqual(sequence.value, 1)

    def test_only_one_sequence_exists(self):
        OrderNumberSequence.objects.create()

        with self.assertRaises(IntegrityError):
            OrderNumberSequence.objects.create()
