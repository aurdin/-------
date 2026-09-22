from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from tests.factories import (
    create_category,
    create_category_group,
    create_currency,
    create_group,
    create_product,
    create_type,
    create_user,
)


class OrderAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(
            username="api_user",
            password="test-password-123",
        )
        cls.other_user = create_user(
            username="other_api_user",
            password="test-password-123",
        )
        cls.currency = create_currency()

        cls.category = create_category(
            name="Для дома",
        )
        cls.group = create_group(
            name="Электроустановочные изделия",
        )
        create_category_group(
            category=cls.category,
            group=cls.group,
        )

        cls.type = create_type(
            name="Вилка",
        )

        cls.product = create_product(
            article="TEST-API-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
        )

    def make_order(self, customer, number):
        return Order.objects.create(
            customer=customer,
            currency=self.currency,
            number=number,
            customer_name="Иван Иванов",
            customer_phone="+380501234567",
            delivery_first_name="Иван",
            delivery_last_name="Иванов",
            delivery_middle_name="Иванович",
            delivery_phone="+380501234567",
            delivery_country="Украина",
            delivery_region="Днепропетровская область",
            delivery_city="Днепр",
            delivery_postal_code="49000",
            delivery_address_line="ул. Тестовая, 1",
            delivery_apartment="10",
            subtotal=Decimal("500.00"),
            product_discount_total=Decimal("0.00"),
            order_discount=Decimal("50.00"),
            promotion_discount=Decimal("0.00"),
            total=Decimal("450.00"),
        )

    def test_order_list_requires_authentication(self):
        """Неавторизованный пользователь не может получить список заказов."""
        client = APIClient()

        response = client.get("/api/orders/")

        self.assertEqual(response.status_code, 403)

    def test_order_detail_requires_authentication(self):
        """Неавторизованный пользователь не может получить заказ."""
        order = self.make_order(
            self.user,
            "ORD-API-000001",
        )
        client = APIClient()

        response = client.get(
            f"/api/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_without_orders_gets_empty_list(self):
        """Авторизованный пользователь без заказов получает пустой список."""
        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.get("/api/orders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_user_sees_only_own_orders(self):
        """Пользователь видит только собственные заказы."""
        own_order = self.make_order(
            self.user,
            "ORD-API-000002",
        )
        self.make_order(
            self.other_user,
            "ORD-API-000003",
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.get("/api/orders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            own_order.id,
        )

    def test_user_cannot_retrieve_other_users_order(self):
        """Пользователь не может получить заказ другого пользователя."""
        other_order = self.make_order(
            self.other_user,
            "ORD-API-000004",
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.get(
            f"/api/orders/{other_order.id}/",
        )

        self.assertEqual(response.status_code, 404)

    def test_order_detail_contains_items(self):
        """Детальная информация о заказе содержит его элементы."""
        order = self.make_order(
            self.user,
            "ORD-API-000005",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("250.00"),
            discount=Decimal("50.00"),
            total=Decimal("400.00"),
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.get(
            f"/api/orders/{order.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["id"],
            order.id,
        )
        self.assertEqual(
            response.data["number"],
            "ORD-API-000005",
        )

        self.assertEqual(
            response.data["subtotal"],
            "500.00",
        )
        self.assertEqual(
            response.data["product_discount_total"],
            "0.00",
        )
        self.assertEqual(
            response.data["order_discount"],
            "50.00",
        )
        self.assertEqual(
            response.data["promotion_discount"],
            "0.00",
        )
        self.assertEqual(
            response.data["total"],
            "450.00",
        )

        self.assertEqual(
            len(response.data["items"]),
            1,
        )
        self.assertEqual(
            response.data["items"][0]["product"],
            self.product.id,
        )
        self.assertEqual(
            response.data["items"][0]["quantity"],
            2,
        )
        self.assertEqual(
            response.data["items"][0]["discount"],
            "50.00",
        )
        self.assertEqual(
            response.data["items"][0]["total"],
            "400.00",
        )

