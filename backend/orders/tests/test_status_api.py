from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderStatus
from orders.tests.factories import create_currency, create_user


class OrderStatusAPITests(APITestCase):
    def setUp(self):
        self.currency = create_currency()

        self.customer = create_user(
            username="customer",
            email="customer@example.com",
        )

        self.staff = create_user(
            username="staff",
            email="staff@example.com",
        )
        self.staff.is_staff = True
        self.staff.save(update_fields=("is_staff",))

        self.other_customer = create_user(
            username="othercustomer",
            email="other@example.com",
        )

    def create_order(self, customer, status=OrderStatus.NEW, number=None):
        if number is None:
            number = f"TEST-{Order.objects.count() + 1:06d}"

        return Order.objects.create(
            customer=customer,
            currency=self.currency,
            number=number,
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

    def test_unauthenticated_user_cannot_change_status(self):
        order = self.create_order(self.customer)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {"status": OrderStatus.CONFIRMED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_change_order_status(self):
        order = self.create_order(self.customer)

        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {"status": OrderStatus.CONFIRMED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_change_order_status(self):
        order = self.create_order(self.customer)

        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {"status": OrderStatus.CONFIRMED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CONFIRMED)

    
    def test_invalid_status_transition_returns_400(self):
        order = self.create_order(
            self.customer,
            status=OrderStatus.CONFIRMED,
        )

        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {"status": OrderStatus.NEW},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CONFIRMED)

    def test_unknown_status_returns_400(self):
        order = self.create_order(self.customer)

        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {"status": "unknown"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.NEW)

    def test_status_field_is_required(self):
        order = self.create_order(self.customer)

        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            f"/api/orders/{order.pk}/status/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.NEW)
