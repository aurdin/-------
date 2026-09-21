from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from catalog.models import Category, CategoryGroup, Group, Product, Type
from orders.models import Order, OrderItem, OrderStatus
from orders.serializers import OrderItemSerializer, OrderSerializer


User = get_user_model()


class OrderModelTest(TestCase): # Тест модели Order
    @classmethod
    def setUpTestData(cls): 
        # Создание тестовых данных для модели Order
        cls.user = User.objects.create_user(
            username="order_user",
            password="test-password-123",
        )
        # Связь категории, группы, типа и продукта
        cls.category = Category.objects.create(
            name="Для дома",
        )
        cls.group = Group.objects.create(
            name="Электроустановочные изделия",
        )
        CategoryGroup.objects.create(
            category=cls.category,
            group=cls.group,
        )
        cls.type = Type.objects.create(
            name="Вилка",
        )
        # Создание тестового продукта
        cls.product = Product.objects.create(
            article="TEST-ORDER-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
            sales_unit="шт.",
        )

    def make_order(self, **kwargs): # Тест создания заказа 
        data = {
            "customer": self.user,
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
            "discount_total": Decimal("50.00"),
            "total": Decimal("450.00"),
        }
        data.update(kwargs)
        return Order.objects.create(**data)
    # Тесты модели Order
    def test_order_created_with_new_status(self): 
        """Проверяет, что новый заказ создаётся со статусом NEW"""
        order = self.make_order()

        self.assertEqual(order.status, OrderStatus.NEW)
        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.total, Decimal("450.00"))

    def test_order_number_is_unique(self): # Тест уникальности номера заказа
        self.make_order()

        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000001",
            )

    def test_order_item_created(self): 
        """Проверяет, что элемент заказа создаётся корректно"""
        order = self.make_order()

        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            article=self.product.article,
            product_name="Тестовая вилка",
            quantity=2,
            unit_price=Decimal("250.00"),
            discount=Decimal("50.00"),
            total=Decimal("450.00"),
        )

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.total, Decimal("450.00"))

    def test_same_product_cannot_be_added_twice_to_order(self): 
        """Проверяет, что в один заказ нельзя добавить два одинаковых продукта"""
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
        """Проверяет, что в элементе заказа нельзя указать нулевое количество"""
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

    def test_negative_discount_is_rejected(self): 
        """Проверяет, что в заказе нельзя указать отрицательную скидку"""
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000002",
                discount_total=Decimal("-1.00"),
            )

    def test_discount_greater_than_subtotal_is_rejected(self): 
        """Проверяет, что в заказе нельзя указать скидку больше, чем стоимость заказа"""
        with self.assertRaises(IntegrityError):
            self.make_order(
                number="ORD-20260917-000003",
                subtotal=Decimal("100.00"),
                discount_total=Decimal("101.00"),
                total=Decimal("-1.00"),
            )

    def test_item_discount_greater_than_item_subtotal_is_rejected(self): 
        """Проверяет, что в элементе заказа нельзя указать скидку больше, чем стоимость элемента"""
        order = self.make_order()

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                article=self.product.article,
                product_name="Тестовая вилка",
                quantity=1,
                unit_price=Decimal("250.00"),
                discount=Decimal("251.00"),
                total=Decimal("1.00"),
            )

    def test_customer_cannot_be_deleted_when_order_exists(self): 
        """Проверяет, что пользователя нельзя удалить, если у него есть заказы"""
        self.make_order()

        with self.assertRaises(IntegrityError):
            self.user.delete()

    def test_product_cannot_be_deleted_when_order_item_exists(self): 
        """Проверяет, что продукт нельзя удалить, если к нему привязан элемент заказа"""
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
        """Проверяет, что при удалении заказа удаляются связанные с ним элементы заказа"""
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
            OrderItem.objects.filter(order_id=order_id).count(),
            1,
        )

        order.delete()

        self.assertEqual(
            OrderItem.objects.filter(order_id=order_id).count(),
            0,
        )

    

    def test_order_keeps_customer_and_delivery_snapshot(self): 
        """Проверяет, что заказ сохраняет снимок клиента и доставки на момент создания"""
        order = self.make_order()

        original_customer_name = order.customer_name
        original_delivery_city = order.delivery_city
        original_delivery_address = order.delivery_address_line

        self.user.username = "changed_user"
        self.user.save()

        order.refresh_from_db()

        self.assertEqual(order.customer_name, original_customer_name)
        self.assertEqual(order.delivery_city, original_delivery_city)
        self.assertEqual(
            order.delivery_address_line,
            original_delivery_address,
        )

class OrderSerializerTest(TestCase): 
    # Тест сериализатора Order
    @classmethod
    def setUpTestData(cls): 
        # Создание тестовых данных для сериализатора Order
        cls.user = User.objects.create_user(
            username="serializer_user",
            password="test-password-123",
        )
        cls.category = Category.objects.create(name="Для дома")
        cls.group = Group.objects.create(name="Электроустановочные изделия")
        CategoryGroup.objects.create(
            category=cls.category,
            group=cls.group,
        )
        cls.type = Type.objects.create(name="Вилка")
        cls.product = Product.objects.create(
            article="TEST-SERIALIZER-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
            sales_unit="шт.",
        )

        cls.order = Order.objects.create(
            customer=cls.user,
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
            discount_total=Decimal("50.00"),
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
            total=Decimal("450.00"),
        )

    def test_order_item_serializer(self): # Тест поля items в сериализаторе Order
        serializer = OrderItemSerializer(self.item)
        data = serializer.data

        self.assertEqual(data["product"], self.product.id)
        self.assertEqual(data["article"], self.product.article)
        self.assertEqual(data["product_name"], "Тестовая вилка")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(data["unit_price"], "250.00")
        self.assertEqual(data["discount"], "50.00")
        self.assertEqual(data["total"], "450.00")

    def test_order_serializer_contains_items(self): # Тест того, что в сериализаторе Order поле items содержит данные о товарах
        serializer = OrderSerializer(self.order)
        data = serializer.data

        self.assertEqual(data["id"], self.order.id)
        self.assertEqual(data["number"], "ORD-SERIALIZER-000001")
        self.assertEqual(data["status"], "new")
        self.assertEqual(data["customer_name"], "Иван Иванов")
        self.assertEqual(data["subtotal"], "500.00")
        self.assertEqual(data["discount_total"], "50.00")
        self.assertEqual(data["total"], "450.00")

        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(
            data["items"][0]["product"],
            self.product.id,
        )

    def test_order_serializer_fields_are_read_only(self): 
        """Проверяет, что все поля сериализатора Order доступны только для чтения"""
        serializer = OrderSerializer(self.order)

        for field_name in serializer.fields:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"Field '{field_name}' must be read-only",
            )

    def test_order_item_serializer_fields_are_read_only(self): 
        """Проверяет, что все поля сериализатора OrderItem доступны только для чтения"""
        serializer = OrderItemSerializer(self.item)

        for field_name in serializer.fields:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"Field '{field_name}' must be read-only",
            )

    def test_order_serializer_handles_multiple_items(self):
         # Тест сериализатора Order с несколькими товарами
        product_2 = Product.objects.create(
            article="TEST-SERIALIZER-002",
            category=self.category,
            group=self.group,
            type=self.type,
            sales_unit="шт.",
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
            data["items"][0]["order"]
            if "order" in data["items"][0]
            else None,
            None,
        )


