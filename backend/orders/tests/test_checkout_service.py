from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from cart.models import Cart, CartItem, CartStatus
from orders.models import Order, OrderStatus
from prices.models import Price

from orders.tests.factories import (
    create_currency,
    create_product,
    create_user,
)
from catalog.services.product_name import ProductNameService


class CheckoutServiceTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="checkout_service_user",
            email="checkout_service@example.com",
        )
        self.currency = create_currency()

        self.product = create_product(
            article="CHECKOUT-SERVICE-001",
        )

        Price.objects.create(
            product=self.product,
            currency=self.currency,
            amount=Decimal("100.00"),
            valid_from=timezone.now(),
        )

        self.cart = Cart.objects.create(
            customer=self.user,
            status=CartStatus.BUSY,
        )

        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )

    def test_checkout_creates_order_and_items_and_clears_cart(self):
        at = timezone.now()
        order_data = {
            "customer_name": "Иван Иванов",
            "customer_phone": "+380501234567",
            "delivery_first_name": "Иван",
            "delivery_last_name": "Иванов",
            "delivery_country": "Украина",
            "delivery_city": "Днепр",
            "delivery_address_line": "ул. Тестовая, 1",
        }

        # Сервис Checkout будет добавлен следующим шагом.
        from orders.services import create_order_from_cart

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        self.assertIsInstance(order, Order)
        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.currency, self.currency)
        self.assertIsNone(order.exchange_rate)
        self.assertEqual(order.status, OrderStatus.NEW)
        
        self.assertEqual(
            order.number,
            "SMEL-" + timezone.now().strftime("%Y%m%d") + "-000001",
        )

        self.assertEqual(order.subtotal, Decimal("200.00"))
        self.assertEqual(order.product_discount_total, Decimal("0.00"))
        self.assertEqual(order.order_discount, Decimal("0.00"))
        self.assertEqual(order.promotion_discount, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("200.00"))

        item = order.items.get()

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.article, self.product.article)
        self.assertEqual(
            item.product_name,
            ProductNameService.build(self.product),
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.discount, Decimal("0.00"))
        self.assertEqual(item.total, Decimal("200.00"))

        self.assertFalse(
            CartItem.objects.filter(cart=self.cart).exists()
        )
