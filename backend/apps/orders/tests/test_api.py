from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.orders.tests.factories import (
    create_category,
    create_category_group,
    create_currency,
    create_group,
    create_product,
    create_type,
    create_user,
)
from django.utils import timezone

from apps.cart.models import Cart, CartItem, CartStatus
from apps.prices.models import Currency, Discount, ExchangeRate, Price


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

    def test_checkout_creates_order(self):
        """Checkout создаёт заказ из текущей корзины."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
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
            },
            format="json",
        )
        print(response.data)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            Order.objects.filter(
                customer=self.user,
            ).count(),
            1,
        )

        order = Order.objects.get(
            customer=self.user,
        )

        self.assertEqual(
            order.currency_id,
            self.currency.id,
        )
        self.assertEqual(
            order.subtotal,
            Decimal("200.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("200.00"),
        )

        self.assertEqual(
            order.items.count(),
            1,
        )

        self.assertEqual(
            order.items.get().quantity,
            2,
        )

        cart.refresh_from_db()

        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_checkout_allows_guest_user(self):
        """Гость может оформить заказ."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        client = APIClient()

        session = client.session
        session.create()
        session.save()
        session_key = session.session_key
        client.cookies["sessionid"] = session_key

        cart = Cart.objects.create(
            session_key=session_key,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
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
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get()

        self.assertIsNone(order.customer_id)
        self.assertEqual(
            order.currency_id,
            self.currency.id,
        )
        self.assertEqual(
            order.total,
            Decimal("100.00"),
        )

        cart.refresh_from_db()


        self.assertIsNone(cart.session_key)
        self.assertEqual(
            cart.status,
            CartStatus.FREE,
        )
        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_checkout_rejects_empty_cart(self):
        """Checkout отклоняется для пустой корзины."""
        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"detail": "Cart is empty."},
        )

        self.assertFalse(
            Order.objects.filter(
                customer=self.user,
            ).exists()
        ) 

    def test_checkout_rejects_excessive_discounts(self):
        """Checkout отклоняет скидки, превышающие остаток заказа."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=timezone.now(),
            is_active=True,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "181.00",
                "promotion_discount": "0.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                "detail": (
                    "Order discounts exceed the remaining order amount."
                )
            },
        )

        self.assertFalse(
            Order.objects.filter(
                customer=self.user,
            ).exists()
        )

    def test_checkout_applies_order_discount(self):
        """Checkout применяет допустимую скидку заказа."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "20.00",
                "promotion_discount": "0.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(
            customer=self.user,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("200.00"),
        )
        self.assertEqual(
            order.product_discount_total,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.order_discount,
            Decimal("20.00"),
        )
        self.assertEqual(
            order.promotion_discount,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("180.00"),
        ) 

    def test_checkout_applies_promotion_discount(self):
        """Checkout применяет допустимую скидку по акции."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "20.00",
                "promotion_discount": "10.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(
            customer=self.user,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("200.00"),
        )
        self.assertEqual(
            order.product_discount_total,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.order_discount,
            Decimal("20.00"),
        )
        self.assertEqual(
            order.promotion_discount,
            Decimal("10.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("170.00"),
        ) 

    def test_checkout_allows_discounts_equal_to_remaining_amount(self):
        """Checkout допускает скидки, полностью обнуляющие сумму заказа."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "150.00",
                "promotion_discount": "50.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            customer=self.user,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("200.00"),
        )
        self.assertEqual(
            order.product_discount_total,
            Decimal("0.00"),
        )
        self.assertEqual(
            order.order_discount,
            Decimal("150.00"),
        )
        self.assertEqual(
            order.promotion_discount,
            Decimal("50.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("0.00"),
        )
    def test_checkout_rejects_negative_order_discount(self):
        """Checkout отклоняет отрицательную скидку заказа."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "-10.00",
                "promotion_discount": "0.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertIn(
            "order_discount",
            response.data,
        )
        self.assertFalse(
            Order.objects.filter(
                customer=self.user,
            ).exists(),
        )

    def test_checkout_rejects_negative_promotion_discount(self):
        """Checkout отклоняет отрицательную скидку по акции."""
        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
                "order_discount": "0.00",
                "promotion_discount": "-10.00",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertIn(
            "promotion_discount",
            response.data,
        )
        self.assertFalse(
            Order.objects.filter(
                customer=self.user,
            ).exists(),
        )

    def test_checkout_converts_price_to_selected_currency(self):
        """Checkout конвертирует цену товара в выбранную валюту."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        print(response.data)

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            customer=self.user,
        )

        self.assertEqual(
            order.currency_id,
            usd.id,
        )

        self.assertEqual(
            order.exchange_rate,
            Decimal("40.00000000"),
        )

        self.assertEqual(
            order.items.get().unit_price,
            Decimal("2.50"),
        )

    def test_checkout_stores_all_order_amounts_in_selected_currency(self):
        """Checkout хранит все денежные значения заказа в выбранной валюте."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(customer=self.user)
        item = order.items.get()

        self.assertEqual(order.currency_id, usd.id)
        self.assertEqual(order.exchange_rate, Decimal("40.00000000"))

        self.assertEqual(order.subtotal, Decimal("5.00"))
        self.assertEqual(order.product_discount_total, Decimal("0.00"))
        self.assertEqual(order.order_discount, Decimal("0.00"))
        self.assertEqual(order.promotion_discount, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("5.00"))

        self.assertEqual(item.unit_price, Decimal("2.50"))
        self.assertEqual(item.discount, Decimal("0.00"))
        self.assertEqual(item.total, Decimal("5.00"))

    def test_checkout_converts_product_discount_to_selected_currency(self):
        """Checkout конвертирует товарную скидку в выбранную валюту."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=now,
            is_active=True,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(customer=self.user)
        item = order.items.get()

        self.assertEqual(order.currency_id, usd.id)
        self.assertEqual(order.exchange_rate, Decimal("40.00000000"))

        self.assertEqual(order.subtotal, Decimal("4.50"))
        self.assertEqual(
            order.product_discount_total,
            Decimal("0.50"),
        )
        self.assertEqual(order.order_discount, Decimal("0.00"))
        self.assertEqual(order.promotion_discount, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("4.50"))

        self.assertEqual(item.unit_price, Decimal("2.25"))
        self.assertEqual(item.discount, Decimal("0.25"))
        self.assertEqual(item.total, Decimal("4.50"))

    def test_checkout_applies_order_and_promotion_discounts_in_selected_currency(self):
        """Checkout применяет скидки заказа и акции в выбранной валюте."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "order_discount": "1.00",
                "promotion_discount": "0.50",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(customer=self.user)
        item = order.items.get()

        self.assertEqual(order.currency_id, usd.id)
        self.assertEqual(order.exchange_rate, Decimal("40.00000000"))

        self.assertEqual(order.subtotal, Decimal("5.00"))
        self.assertEqual(
            order.product_discount_total,
            Decimal("0.00"),
        )
        self.assertEqual(order.order_discount, Decimal("1.00"))
        self.assertEqual(order.promotion_discount, Decimal("0.50"))
        self.assertEqual(order.total, Decimal("3.50"))

        self.assertEqual(item.unit_price, Decimal("2.50"))
        self.assertEqual(item.discount, Decimal("0.00"))
        self.assertEqual(item.total, Decimal("5.00"))

    def test_checkout_allows_discounts_equal_to_usd_order_amount(self):
        """Checkout допускает скидки, полностью покрывающие USD-сумму заказа."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "order_discount": "3.00",
                "promotion_discount": "2.00",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(customer=self.user)

        self.assertEqual(order.currency_id, usd.id)
        self.assertEqual(order.exchange_rate, Decimal("40.00000000"))
        self.assertEqual(order.subtotal, Decimal("5.00"))
        self.assertEqual(order.product_discount_total, Decimal("0.00"))
        self.assertEqual(order.order_discount, Decimal("3.00"))
        self.assertEqual(order.promotion_discount, Decimal("2.00"))
        self.assertEqual(order.total, Decimal("0.00"))

    def test_checkout_rejects_excessive_usd_discounts(self):
        """Checkout отклоняет скидки, превышающие USD-сумму заказа."""
        usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            is_active=True,
        )

        now = timezone.now()

        ExchangeRate.objects.create(
            base_currency=self.currency,
            quote_currency=usd,
            rate=Decimal("40.00000000"),
            valid_from=now,
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=now,
        )

        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(
            user=self.user,
        )

        response = client.post(
            "/api/checkout/",
            {
                "currency": "USD",
                "order_discount": "3.01",
                "promotion_discount": "2.00",
                "customer_name": "Иван Иванов",
                "customer_phone": "+380501234567",
                "delivery_first_name": "Иван",
                "delivery_last_name": "Иванов",
                "delivery_country": "Украина",
                "delivery_city": "Днепр",
                "delivery_address_line": "ул. Тестовая, 1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                "detail": "Order discounts exceed the remaining order amount.",
            },
        )

        self.assertFalse(Order.objects.filter(customer=self.user).exists())            
