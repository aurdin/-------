from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Group, Product, Type
from cart.models import Cart, CartItem


User = get_user_model()


class CartAuthenticationIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123",
        )

        self.category = Category.objects.create(
            name="Test Category",
        )

        self.group = Group.objects.create(
            name="Test Group",
        )

        self.type = Type.objects.create(
            name="Test Type",
        )

        self.product_a = Product.objects.create(
            article="AUTH-TEST-001",
            category=self.category,
            group=self.group,
            type=self.type,
            sales_unit="шт.",
        )

        self.product_b = Product.objects.create(
            article="AUTH-TEST-002",
            category=self.category,
            group=self.group,
            type=self.type,
            sales_unit="шт.",
        )

    def test_guest_cart_is_created_for_session(self):
        response = self.client.get("/api/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(self.client.session.session_key)

        cart = Cart.objects.get(session_key=self.client.session.session_key)

        self.assertIsNone(cart.customer_id)
        self.assertEqual(cart.items.count(), 0)

    def test_login_transfers_guest_cart_to_customer_when_personal_cart_does_not_exist(
        self,
    ):
        # Создаём гостевую корзину.
        response = self.client.get("/api/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        guest_session_key = self.client.session.session_key

        # Добавляем товар гостю.
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product_a.id,
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        guest_cart = Cart.objects.get(session_key=guest_session_key)

        self.assertEqual(
            guest_cart.items.get(product=self.product_a).quantity,
            3,
        )

        # Выполняем вход.
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # Гостевая корзина должна стать персональной.
        personal_cart = Cart.objects.get(customer=self.user)

        self.assertIsNone(personal_cart.session_key)

        item = personal_cart.items.get(product=self.product_a)

        self.assertEqual(
            item.quantity,
            3,
        )

        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

    def test_login_merges_guest_cart_with_existing_personal_cart(self):
        # Создаём персональную корзину пользователя.
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        CartItem.objects.create(
            cart=personal_cart,
            product=self.product_a,
            quantity=2,
        )

        # Создаём гостевую корзину.
        response = self.client.get("/api/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        guest_session_key = self.client.session.session_key

        # Тот же товар — количества должны сложиться.
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product_a.id,
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        # Второй товар — должен просто добавиться.
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product_b.id,
                "quantity": 4,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        # Выполняем вход.
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        personal_cart.refresh_from_db()

        # Товар A: 2 + 3 = 5.
        self.assertEqual(
            personal_cart.items.get(product=self.product_a).quantity,
            5,
        )

        # Товар B: 4.
        self.assertEqual(
            personal_cart.items.get(product=self.product_b).quantity,
            4,
        )

        # Гостевая корзина должна быть удалена.
        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

        self.assertEqual(
            personal_cart.items.count(),
            2,
        )

    def test_login_without_guest_cart_creates_personal_cart(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(Cart.objects.filter(customer=self.user).exists())

        personal_cart = Cart.objects.get(customer=self.user)

        self.assertEqual(
            personal_cart.items.count(),
            0,
        )

    def test_authenticated_cart_is_used_after_login(self):
        # Создаём гостевую корзину и добавляем товар.
        response = self.client.get("/api/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        guest_session_key = self.client.session.session_key

        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product_a.id,
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        # Вход.
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # Запрашиваем текущую корзину уже как авторизованный пользователь.
        response = self.client.get("/api/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["items"][0]["product"]["id"],
            self.product_a.id,
        )

        self.assertEqual(
            response.data["items"][0]["quantity"],
            2,
        )

        # У пользователя ровно одна персональная корзина.
        self.assertEqual(
            Cart.objects.filter(customer=self.user).count(),
            1,
        )

        # Старой гостевой корзины нет.
        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())
