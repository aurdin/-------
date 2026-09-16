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

        personal_cart = Cart.objects.get(customer=self.user)

        self.assertIsNone(personal_cart.session_key)

        item = personal_cart.items.get(product=self.product_a)

        self.assertEqual(
            item.quantity,
            3,
        )

        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

    def test_login_merges_guest_cart_with_existing_personal_cart(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        CartItem.objects.create(
            cart=personal_cart,
            product=self.product_a,
            quantity=2,
        )

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
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

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

        self.assertEqual(
            personal_cart.items.get(product=self.product_a).quantity,
            5,
        )

        self.assertEqual(
            personal_cart.items.get(product=self.product_b).quantity,
            4,
        )

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

        self.assertEqual(
            Cart.objects.filter(customer=self.user).count(),
            1,
        )

        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

    # ------------------------------------------------------------------
    # Registration + automatic login + cart integration
    # ------------------------------------------------------------------

    def test_register_without_guest_cart_creates_personal_cart_and_logs_in(
        self,
    ):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewStrongPass123",
                "password_confirm": "NewStrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        new_user = User.objects.get(username="newuser")

        self.assertEqual(
            response.data["id"],
            new_user.id,
        )

        self.assertEqual(
            response.data["username"],
            "newuser",
        )

        self.assertTrue(Cart.objects.filter(customer=new_user).exists())

        personal_cart = Cart.objects.get(customer=new_user)

        self.assertEqual(
            personal_cart.items.count(),
            0,
        )

        # Проверяем автоматическую авторизацию.
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            new_user.id,
        )

        self.assertEqual(
            response.data["username"],
            "newuser",
        )

    def test_register_transfers_guest_cart_to_personal_cart(self):
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

        # Регистрируем нового пользователя.
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewStrongPass123",
                "password_confirm": "NewStrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        new_user = User.objects.get(username="newuser")

        # Guest cart должна стать personal cart.
        personal_cart = Cart.objects.get(customer=new_user)

        self.assertIsNone(personal_cart.session_key)

        item = personal_cart.items.get(product=self.product_a)

        self.assertEqual(
            item.quantity,
            3,
        )

        # Guest cart больше не существует.
        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

        # Пользователь автоматически авторизован.
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            new_user.id,
        )

        # /api/cart/ должен вернуть personal cart.
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
            3,
        )

    def test_register_merges_guest_cart_with_existing_personal_cart(self):
        # Это отдельный пользователь, для которого заранее
        # существует персональная корзина.
        existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="ExistingPass123",
        )

        personal_cart = Cart.objects.create(
            customer=existing_user,
            status=True,
        )

        CartItem.objects.create(
            cart=personal_cart,
            product=self.product_a,
            quantity=2,
        )

        # Важное ограничение:
        # обычная регистрация создаёт нового пользователя,
        # поэтому существующая personal cart не может
        # принадлежать регистрируемому пользователю.
        #
        # Этот тест проверяет отдельный сценарий:
        # после регистрации новая personal cart создаётся
        # независимо от корзины другого пользователя.
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewStrongPass123",
                "password_confirm": "NewStrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        new_user = User.objects.get(username="newuser")

        new_personal_cart = Cart.objects.get(customer=new_user)

        self.assertNotEqual(
            new_personal_cart.id,
            personal_cart.id,
        )

        self.assertEqual(
            new_personal_cart.items.count(),
            0,
        )

        # Корзина существующего пользователя не изменилась.
        personal_cart.refresh_from_db()

        self.assertEqual(
            personal_cart.items.get(product=self.product_a).quantity,
            2,
        )

    def test_register_with_guest_cart_and_existing_personal_cart_is_not_possible_for_new_user(
        self,
    ):
        # При регистрации создаётся новый пользователь.
        # Поэтому "существующая personal cart" для него
        # до регистрации невозможна.
        #
        # Реальное объединение с существующей personal cart
        # уже проверено Login-тестом выше.

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
                "quantity": 4,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewStrongPass123",
                "password_confirm": "NewStrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        new_user = User.objects.get(username="newuser")

        personal_cart = Cart.objects.get(customer=new_user)

        self.assertEqual(
            personal_cart.items.get(product=self.product_a).quantity,
            4,
        )

        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            new_user.id,
        )
