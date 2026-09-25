from django.test import TestCase

from orders.models import Order, OrderStatus
from orders.services import change_order_status
from orders.tests.factories import create_currency, create_user


class OrderStatusServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.currency = create_currency()

    def create_order(self, status=OrderStatus.NEW):
        return Order.objects.create(
            customer=self.user,
            currency=self.currency,
            number=f"TEST-{Order.objects.count() + 1:06d}",
            status=status,
            customer_name="Тестовый клиент",
            customer_phone="+380501234567",
            delivery_first_name="Иван",
            delivery_last_name="Иванов",
            delivery_phone="+380501234567",
            delivery_country="Украина",
            delivery_city="Днепр",
            delivery_address_line="ул. Тестовая, 1",
            subtotal="100.00",
            product_discount_total="0.00",
            order_discount="0.00",
            promotion_discount="0.00",
            total="100.00",
        )

    def test_new_to_confirmed(self):
        order = self.create_order(OrderStatus.NEW)

        change_order_status(order, OrderStatus.CONFIRMED)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CONFIRMED)

    def test_confirmed_to_processing(self):
        order = self.create_order(OrderStatus.CONFIRMED)

        change_order_status(order, OrderStatus.PROCESSING)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PROCESSING)

    def test_processing_to_completed(self):
        order = self.create_order(OrderStatus.PROCESSING)

        change_order_status(order, OrderStatus.COMPLETED)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.COMPLETED)

    def test_new_can_be_cancelled(self):
        order = self.create_order(OrderStatus.NEW)

        change_order_status(order, OrderStatus.CANCELLED)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_confirmed_can_be_cancelled(self):
        order = self.create_order(OrderStatus.CONFIRMED)

        change_order_status(order, OrderStatus.CANCELLED)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_processing_can_be_cancelled(self):
        order = self.create_order(OrderStatus.PROCESSING)

        change_order_status(order, OrderStatus.CANCELLED)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_backward_transition_is_forbidden(self):
        order = self.create_order(OrderStatus.CONFIRMED)

        with self.assertRaises(ValueError):
            change_order_status(order, OrderStatus.NEW)

    def test_completed_is_terminal(self):
        order = self.create_order(OrderStatus.COMPLETED)

        with self.assertRaises(ValueError):
            change_order_status(order, OrderStatus.CANCELLED)

    def test_cancelled_is_terminal(self):
        order = self.create_order(OrderStatus.CANCELLED)

        with self.assertRaises(ValueError):
            change_order_status(order, OrderStatus.CONFIRMED)
def change_order_status(order, new_status):
    allowed_transitions = {
        OrderStatus.NEW: {
            OrderStatus.CONFIRMED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.CONFIRMED: {
            OrderStatus.PROCESSING,
            OrderStatus.CANCELLED,
        },
        OrderStatus.PROCESSING: {
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.COMPLETED: set(),
        OrderStatus.CANCELLED: set(),
    }

    if new_status not in allowed_transitions.get(order.status, set()):
        raise ValueError(
            f"Invalid order status transition: "
            f"{order.status} -> {new_status}"
        )

    order.status = new_status
    order.save(update_fields=("status", "updated_at"))

    return order

    