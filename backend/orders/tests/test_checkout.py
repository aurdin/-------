from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from cart.models import Cart, CartItem, CartStatus
from orders.models import Order, OrderStatus
from prices.models import Price

from orders.tests.factories import (
    create_currency,
    create_product,
    create_user,
)


class CheckoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = create_user(
            username="checkout_user",
            email="checkout@example.com",
        )
        self.currency = create_currency()

        self.product = create_product(
            article="CHECKOUT-001",
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        self.client.force_authenticate(user=self.user)

    def test_checkout_creates_order_and_clears_cart(self):
        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.post(
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

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get()

        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.currency, self.currency)
        self.assertIsNone(order.exchange_rate)
        self.assertEqual(order.status, OrderStatus.NEW)

        self.assertEqual(order.subtotal, Decimal("200.00"))
        self.assertEqual(order.product_discount_total, Decimal("0.00"))
        self.assertEqual(order.order_discount, Decimal("0.00"))
        self.assertEqual(order.promotion_discount, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("200.00"))

        item = order.items.get()

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.article, self.product.article)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.discount, Decimal("0.00"))
        self.assertEqual(item.total, Decimal("200.00"))
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

    def test_checkout_requires_currency(self):
        response = self.client.post(
            "/api/checkout/",
            {
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
        self.assertIn("currency", response.data) 

    def test_checkout_rejects_invalid_currency(self):
        response = self.client.post(
            "/api/checkout/",
            {
                "currency": "XXX",
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
        self.assertIn("currency", response.data)

    def test_checkout_rejects_empty_cart(self):
        Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        response = self.client.post(
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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Cart is empty.",
        )
        self.assertFalse(Order.objects.exists())

    def test_checkout_rejects_product_without_current_price(self):
        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        Price.objects.all().delete()

        response = self.client.post(
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

        self.assertEqual(response.status_code, 400)
        self.assertIn("No current price", response.data["detail"])
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(cart=cart).exists())

    def test_guest_checkout_creates_order(self):
        self.client.force_authenticate(user=None)

        session = self.client.session
        session.create()
        session_key = session.session_key

        self.client.cookies["sessionid"] = session_key

        cart = Cart.objects.create(
            session_key=session_key,
            status=CartStatus.BUSY,
        )
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
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
        # print("GUEST CHECKOUT RESPONSE:", response.status_code, response.data)

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get()

        self.assertIsNone(order.customer)
        self.assertEqual(order.customer_name, "Иван Иванов")
        self.assertEqual(order.customer_phone, "+380501234567")
        self.assertEqual(order.total, Decimal("100.00"))

        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

        cart.refresh_from_db()

        self.assertEqual(cart.status, CartStatus.FREE)
        self.assertIsNone(cart.session_key)
        self.assertIsNone(cart.customer_id)        

    def test_checkout_requires_customer_name(self):
        cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
            "/api/checkout/",
            {
                "currency": self.currency.code,
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