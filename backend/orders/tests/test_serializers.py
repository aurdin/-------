from decimal import Decimal

from django.test import TestCase

from orders.models import Order, OrderItem
from orders.serializers import OrderItemSerializer, OrderSerializer
from tests.factories import (
    create_category,
    create_category_group,
    create_currency,
    create_group,
    create_product,
    create_type,
    create_user,
)


class OrderSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(
            username="serializer_user",
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
            article="TEST-SERIALIZER-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
        )

        cls.order = Order.objects.create(
            customer=cls.user,
            currency=cls.currency,
            number="ORD-SERIALIZER-000001",
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

        cls.item = OrderItem.objects.create(
            order=cls.order,
            product=cls.product,
            article=cls.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("250.00"),
            discount=Decimal("50.00"),
            total=Decimal("400.00"),
        )

    def test_order_item_serializer(self):
        serializer = OrderItemSerializer(self.item)
        data = serializer.data

        self.assertEqual(data["id"], self.item.id)
        self.assertEqual(data["product"], self.product.id)
        self.assertEqual(data["article"], self.product.article)
        self.assertEqual(data["product_name"], "Тестовая вилка")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(data["unit_price"], "250.00")
        self.assertEqual(data["discount"], "50.00")
        self.assertEqual(data["total"], "400.00")

    def test_order_serializer_contains_items(self):
        serializer = OrderSerializer(self.order)
        data = serializer.data

        self.assertEqual(data["id"], self.order.id)
        self.assertEqual(
            data["number"],
            "ORD-SERIALIZER-000001",
        )
        self.assertEqual(data["status"], "new")
        self.assertEqual(data["currency"], self.currency.id)
        self.assertEqual(
            data["customer_name"],
            "Иван Иванов",
        )
        self.assertEqual(data["subtotal"], "500.00")
        self.assertEqual(
            data["product_discount_total"],
            "0.00",
        )
        self.assertEqual(
            data["order_discount"],
            "50.00",
        )
        self.assertEqual(
            data["promotion_discount"],
            "0.00",
        )
        self.assertEqual(data["total"], "450.00")

        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(
            data["items"][0]["product"],
            self.product.id,
        )

    def test_order_serializer_fields_are_read_only(self):
        """Проверяет, что все поля OrderSerializer доступны только для чтения."""
        serializer = OrderSerializer(self.order)

        for field_name in serializer.fields:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"Field '{field_name}' must be read-only",
            )

    def test_order_item_serializer_fields_are_read_only(self):
        """Проверяет, что все поля OrderItemSerializer доступны только для чтения."""
        serializer = OrderItemSerializer(self.item)

        for field_name in serializer.fields:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"Field '{field_name}' must be read-only",
            )

    def test_order_serializer_handles_multiple_items(self):
        product_2 = create_product(
            article="TEST-SERIALIZER-002",
            category=self.category,
            group=self.group,
            type=self.type,
        )

        OrderItem.objects.create(
            order=self.order,
            product=product_2,
            article=product_2.article,
            product_name="Вторая вилка",
            quantity=1,
            unit_price=Decimal("100.00"),
            discount=Decimal("0.00"),
            total=Decimal("100.00"),
        )

        serializer = OrderSerializer(self.order)
        data = serializer.data

        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(
            data["items"][0]["product"],
            self.product.id,
        )
        self.assertEqual(
            data["items"][1]["product"],
            product_2.id,
        )
