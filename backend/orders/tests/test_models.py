from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from orders.models import Order, OrderItem, OrderStatus
from tests.factories import (
    create_category,
    create_category_group,
    create_currency,
    create_group,
    create_product,
    create_type,
    create_user,
)


class OrderModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user(
            username="order_user",
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
            article="TEST-ORDER-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
        )

    def make_order(self, **kwargs):
        data = {
            "customer": self.user,
            "currency": self.currency,
            "number": "ORD-20260917-000001",
            "customer_name": "Иван Иванов",
            "customer_phone": "+380501234567",
            "delivery_first_name": "Иван",
            "delivery_last_name": "Иванов",
            "delivery_middle_name": "Иванович",
            "delivery_phone": "+380501234567",
            "delivery_country": "Украина",
            "delivery_region": "Днепропетровская область",
            "delivery_city": "Днепр",
            "delivery_postal_code": "49000",
            "delivery_address_line": "ул. Тестовая, 1",
            "delivery_apartment": "10",
            "subtotal": Decimal("500.00"),
            "product_discount_total": Decimal("0.00"),
            "order_discount": Decimal("50.00"),
            "promotion_discount": Decimal("0.00"),
            "total": Decimal("450.00"),
        }
        data.update(kwargs)
        return Order.objects.create(**data)

    # ------------------------------------------------------------------
    # Order
    # ------------------------------------------------------------------

    def test_order_created_with_new_status(self):
        order = self.make_order()

        self.assertEqual(
            order.status,
            OrderStatus.NEW,
        )
        self.assertEqual(
            order.customer,
            self.user,
        )
        self.assertEqual(
            order.total,
            Decimal("450.00"),
        )

    def test_order_number_is_unique(self):
        self.make_order()

        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000001",
            )

    def test_negative_product_discount_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000002",
                product_discount_total=Decimal("-1.00"),
            )

    def test_negative_order_discount_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000003",
                order_discount=Decimal("-1.00"),
            )

    def test_negative_promotion_discount_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000004",
                promotion_discount=Decimal("-1.00"),
            )

    def test_order_discount_and_promotion_cannot_exceed_subtotal(self):
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000005",
                subtotal=Decimal("100.00"),
                order_discount=Decimal("70.00"),
                promotion_discount=Decimal("31.00"),
                total=Decimal("0.00"),
            )

    def test_zero_subtotal_and_total_are_allowed(self):
        order = self.make_order(
            number="ORD-20260917-000006",
            subtotal=Decimal("0.00"),
            product_discount_total=Decimal("100.00"),
            order_discount=Decimal("0.00"),
            promotion_discount=Decimal("0.00"),
            total=Decimal("0.00"),
        )

        self.assertEqual(
            order.subtotal,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("0.00"),
        )

    def test_order_total_zero_is_allowed_with_full_discount(self):
        order = self.make_order(
            number="ORD-20260917-000007",
            subtotal=Decimal("100.00"),
            product_discount_total=Decimal("0.00"),
            order_discount=Decimal("100.00"),
            promotion_discount=Decimal("0.00"),
            total=Decimal("0.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("0.00"),
        )

    # ------------------------------------------------------------------
    # OrderItem
    # ------------------------------------------------------------------

    def test_order_item_created(self):
        order = self.make_order()

        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("250.00"),
            discount=Decimal("50.00"),
            total=Decimal("400.00"),
        )

        self.assertEqual(
            order.items.count(),
            1,
        )
        self.assertEqual(
            item.quantity,
            2,
        )
        self.assertEqual(
            item.total,
            Decimal("400.00"),
        )

    def test_same_product_cannot_be_added_twice_to_order(self):
        order = self.make_order()

        OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=1,
            unit_price=Decimal("250.00"),
            discount=Decimal("0.00"),
            total=Decimal("250.00"),
        )

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                article=self.product.article,
                product_name="Тестовая вилка",
                quantity=1,
                unit_price=Decimal("250.00"),
                discount=Decimal("0.00"),
                total=Decimal("250.00"),
            )

    def test_zero_quantity_is_rejected(self):
        order = self.make_order()

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                article=self.product.article,
                product_name="Тестовая вилка",
                quantity=0,
                unit_price=Decimal("250.00"),
                discount=Decimal("0.00"),
                total=Decimal("250.00"),
            )

    def test_negative_item_discount_is_rejected(self):
        order = self.make_order()

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                article=self.product.article,
                product_name="Тестовая вилка",
                quantity=1,
                unit_price=Decimal("250.00"),
                discount=Decimal("-1.00"),
                total=Decimal("251.00"),
            )

    def test_item_discount_greater_than_unit_price_is_rejected(self):
        order = self.make_order()

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                article=self.product.article,
                product_name="Тестовая вилка",
                quantity=2,
                unit_price=Decimal("250.00"),
                discount=Decimal("250.01"),
                total=Decimal("0.00"),
            )

    def test_full_item_discount_is_allowed(self):
        order = self.make_order()

        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("250.00"),
            discount=Decimal("250.00"),
            total=Decimal("0.00"),
        )

        self.assertEqual(
            item.discount,
            Decimal("250.00"),
        )
        self.assertEqual(
            item.total,
            Decimal("0.00"),
        )

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    def test_customer_cannot_be_deleted_when_order_exists(self):
        self.make_order()

        with self.assertRaises(IntegrityError):
            self.user.delete()

    def test_product_cannot_be_deleted_when_order_item_exists(self):
        order = self.make_order()

        OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=1,
            unit_price=Decimal("250.00"),
            discount=Decimal("0.00"),
            total=Decimal("250.00"),
        )

        with self.assertRaises(IntegrityError):
            self.product.delete()

    def test_deleting_order_deletes_order_items(self):
        order = self.make_order()

        OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=1,
            unit_price=Decimal("250.00"),
            discount=Decimal("0.00"),
            total=Decimal("250.00"),
        )

        order_id = order.id

        self.assertEqual(
            OrderItem.objects.filter(
                order_id=order_id,
            ).count(),
            1,
        )

        order.delete()

        self.assertEqual(
            OrderItem.objects.filter(
                order_id=order_id,
            ).count(),
            0,
        )

    def test_order_keeps_customer_and_delivery_snapshot(self):
        order = self.make_order()

        original_customer_name = order.customer_name
        original_delivery_city = order.delivery_city
        original_delivery_address = order.delivery_address_line

        self.user.username = "changed_user"
        self.user.save()

        order.refresh_from_db()

        self.assertEqual(
            order.customer_name,
            original_customer_name,
        )
        self.assertEqual(
            order.delivery_city,
            original_delivery_city,
        )
        self.assertEqual(
            order.delivery_address_line,
            original_delivery_address,
        )
