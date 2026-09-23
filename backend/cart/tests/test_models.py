from django.contrib.auth import get_user_model # Импортируем функцию get_user_model (получаем пользователя из настроек Django)
from django.db import IntegrityError # Импортируем исключение IntegrityError
from django.test import TestCase # Импортируем класс TestCase (тестовая сущность)

from cart.models import Cart, CartItem # Импортируем модели Cart и CartItem
from catalog.models import (
    Category,
    CategoryGroup,
    Group,
    Product,
    Type,
)


User = get_user_model()


class CartModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="cart_user",
            password="test-password",
        )

        cls.category = Category.objects.create(
            name="Test category",
        )

        cls.group = Group.objects.create(
            name="Test group",
        )

        CategoryGroup.objects.create(
            category=cls.category,
            group=cls.group,
        )

        cls.type = Type.objects.create(
            name="Test type",
        )

        cls.product = Product.objects.create(
            article="CART-TEST-001",
            category=cls.category,
            group=cls.group,
            type=cls.type,
            sales_unit="шт.",
        )

    def test_create_customer_cart(self):
        cart = Cart.objects.create(
            customer=self.user,
        )

        self.assertIsNotNone(cart.pk)
        self.assertEqual(cart.customer, self.user)
        self.assertIsNone(cart.session_key)
        self.assertTrue(cart.status)

    def test_create_guest_cart(self):
        cart = Cart.objects.create(
            session_key="test-session-key",
        )

        self.assertIsNotNone(cart.pk)
        self.assertIsNone(cart.customer)
        self.assertEqual(cart.session_key, "test-session-key")
        self.assertTrue(cart.status)

    def test_cart_without_owner_is_rejected(self):
        with self.assertRaises(IntegrityError):
            Cart.objects.create()

    def test_cart_with_two_owners_is_rejected(self):
        with self.assertRaises(IntegrityError):
            Cart.objects.create(
                customer=self.user,
                session_key="test-session-key",
            )

    def test_create_cart_item(self):
        cart = Cart.objects.create(
            customer=self.user,
        )

        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=3,
        )

        self.assertIsNotNone(item.pk)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.product, self.product)

    def test_zero_quantity_is_rejected(self):
        cart = Cart.objects.create(
            customer=self.user,
        )

        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=cart,
                product=self.product,
                quantity=0,
            )

    def test_duplicate_product_in_cart_is_rejected(self):
        cart = Cart.objects.create(
            customer=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=cart,
                product=self.product,
                quantity=2,
            )

    def test_product_cannot_be_deleted_while_in_cart(self):
        cart = Cart.objects.create(
            customer=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        with self.assertRaises(IntegrityError):
            self.product.delete()
