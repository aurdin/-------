from decimal import Decimal

from django.test import TestCase

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


class CheckoutCalculationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(username="checkout_user")
        cls.currency = create_currency()

        cls.category = create_category(name="Для дома")
        cls.group = create_group(
            name="Электроустановочные изделия"
        )
        create_category_group(
            category=cls.category,
            group=cls.group,
        )

        cls.type = create_type(name="Вилка")

        cls.product = create_product(
            article="TEST-CHECKOUT-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
        )

    def make_order(self, **kwargs):
        data = {
            "customer": self.user,
            "currency": self.currency,
            "number": "ORD-CHECKOUT-000001",
            "customer_name": "Иван Иванов",
            "customer_phone": "+380501234567",
            "delivery_first_name": "Иван",
            "delivery_last_name": "Иванов",
            "delivery_middle_name": "",
            "delivery_phone": "+380501234567",
            "delivery_country": "Украина",
            "delivery_region": "",
            "delivery_city": "Днепр",
            "delivery_postal_code": "",
            "delivery_address_line": "ул. Тестовая, 1",
            "delivery_apartment": "",
            "subtotal": Decimal("1800.00"),
            "product_discount_total": Decimal("0.00"),
            "order_discount": Decimal("0.00"),
            "promotion_discount": Decimal("0.00"),
            "total": Decimal("1800.00"),
        }
        data.update(kwargs)
        return Order.objects.create(**data)

    def test_order_item_discount_is_per_unit(self):
        order = self.make_order()

        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("1000.00"),
            discount=Decimal("100.00"),
            total=Decimal("1800.00"),
        )

        self.assertEqual(
            (item.unit_price - item.discount) * item.quantity,
            Decimal("1800.00"),
        )

    def test_order_discount_and_promotion_are_subtracted_from_subtotal(self):
        subtotal = Decimal("1800.00")
        order_discount = Decimal("100.00")
        promotion_discount = Decimal("50.00")

        total = subtotal - order_discount - promotion_discount

        self.assertEqual(total, Decimal("1650.00"))

    def test_product_discount_is_not_subtracted_from_subtotal_twice(self):
        unit_price = Decimal("1000.00")
        product_discount = Decimal("100.00")
        quantity = 2

        product_discount_total = product_discount * quantity
        subtotal = (unit_price - product_discount) * quantity

        total = subtotal

        self.assertEqual(
            product_discount_total,
            Decimal("200.00"),
        )
        self.assertEqual(
            subtotal,
            Decimal("1800.00"),
        )
        self.assertEqual(
            total,
            Decimal("1800.00"),
        )

    def test_full_calculation(self):
        unit_price = Decimal("1000.00")
        product_discount = Decimal("100.00")
        quantity = 2

        order_discount = Decimal("100.00")
        promotion_discount = Decimal("50.00")

        product_discount_total = product_discount * quantity
        subtotal = (
            unit_price - product_discount
        ) * quantity
        total = (
            subtotal
            - order_discount
            - promotion_discount
        )

        self.assertEqual(
            product_discount_total,
            Decimal("200.00"),
        )
        self.assertEqual(
            subtotal,
            Decimal("1800.00"),
        )
        self.assertEqual(
            total,
            Decimal("1650.00"),
        )
