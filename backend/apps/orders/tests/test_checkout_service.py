from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.cart.models import Cart, CartItem, CartStatus
from apps.orders.models import Order, OrderStatus
from apps.prices.models import Price, Discount

from apps.orders.tests.factories import (
    create_currency,
    create_product,
    create_user,
)
from apps.catalog.services.product_name import ProductNameService
from apps.orders.services import create_order_from_cart

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
        from apps.orders.services import create_order_from_cart

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

    def test_checkout_saves_product_discount_in_order_item(self):
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

        from apps.prices.models import Discount
        from apps.orders.services import create_order_from_cart

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=at,
        )

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        item = order.items.get()

        self.assertEqual(
            item.discount,
            Decimal("10.00"),
        )

    def test_checkout_calculates_product_discount_total(self):
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

        from apps.prices.models import Discount
        from apps.orders.services import create_order_from_cart

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=at,
        )

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("180.00"),
        )

        self.assertEqual(
            order.product_discount_total,
            Decimal("20.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("180.00"),
        )

    def test_checkout_creates_all_order_items_for_multiple_products(self):
        second_product = create_product(
            article="CHECKOUT-SERVICE-002",
        )

        Price.objects.create(
            product=second_product,
            currency=self.currency,
            amount=Decimal("50.00"),
            valid_from=timezone.now(),
        )

        CartItem.objects.create(
            cart=self.cart,
            product=second_product,
            quantity=3,
        )

        at = timezone.now()

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
        }

        from apps.orders.services import create_order_from_cart

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        self.assertEqual(
            order.items.count(),
            2,
        )

        self.assertEqual(
            order.items.get(product=self.product).quantity,
            2,
        )

        self.assertEqual(
            order.items.get(product=second_product).quantity,
            3,
        )                

    def test_checkout_calculates_total_for_multiple_products_with_discount(self):
        from apps.prices.models import Discount

        second_product = create_product(
            article="CHECKOUT-SERVICE-003",
        )

        Price.objects.create(
            product=second_product,
            currency=self.currency,
            amount=Decimal("50.00"),
            valid_from=timezone.now(),
        )

        at = timezone.now()

        Discount.objects.create(
            product=second_product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("20.00"),
            valid_from=at,
        )

        CartItem.objects.create(
            cart=self.cart,
            product=second_product,
            quantity=3,
        )

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
        }

        from apps.orders.services import create_order_from_cart

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("320.00"),
        )
        self.assertEqual(
            order.product_discount_total,
            Decimal("30.00"),
        )
        self.assertEqual(
            order.total,
            Decimal("320.00"),
        ) 

    def test_checkout_saves_correct_values_for_multiple_order_items(self):
        from apps.prices.models import Discount

        second_product = create_product(
            article="CHECKOUT-SERVICE-004",
        )

        Price.objects.create(
            product=second_product,
            currency=self.currency,
            amount=50,
            valid_from=timezone.now(),
        )

        at = timezone.now()

        Discount.objects.create(
            product=second_product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("20.00"),
            valid_from=at,
        )

        CartItem.objects.create(
            cart=self.cart,
            product=second_product,
            quantity=3,
        )

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
        }

        from apps.orders.services import create_order_from_cart

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
        )

        first_item = order.items.get(
            product=self.product,
        )
        second_item = order.items.get(
            product=second_product,
        )

        self.assertEqual(first_item.quantity, 2)
        self.assertEqual(first_item.unit_price, Decimal("100.00"))
        self.assertEqual(first_item.discount, Decimal("0.00"))
        self.assertEqual(first_item.total, Decimal("200.00"))

        self.assertEqual(second_item.quantity, 3)
        self.assertEqual(second_item.unit_price, Decimal("40.00"))
        self.assertEqual(second_item.discount, Decimal("10.00"))
        self.assertEqual(second_item.total, Decimal("120.00"))

    def test_checkout_applies_order_discount_to_total(self):
        from apps.orders.services import create_order_from_cart

        at = timezone.now()

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
            "order_discount": Decimal("20.00"),
        }

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
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

    def test_checkout_applies_promotion_discount_to_total(self):
        from apps.orders.services import create_order_from_cart

        at = timezone.now()

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
            "order_discount": Decimal("20.00"),
            "promotion_discount": Decimal("10.00"),
        }

        order = create_order_from_cart(
            cart=self.cart,
            customer=self.user,
            currency=self.currency,
            order_data=order_data,
            at=at,
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

    def test_checkout_rejects_discounts_exceeding_remaining_amount(self):
        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=timezone.now(),
            is_active=True,
        )

        with self.assertRaises(ValueError):
            create_order_from_cart(
                cart=self.cart,
                customer=self.user,
                currency=self.currency,
                order_data={
                    "customer_name": "Иван Иванов",
                    "customer_phone": "+380501234567",
                    "delivery_first_name": "Иван",
                    "delivery_last_name": "Иванов",
                    "delivery_country": "Украина",
                    "delivery_city": "Днепр",
                    "delivery_address_line": "ул. Центральная, 1",
                    "order_discount": Decimal("181.00"),
                    "promotion_discount": Decimal("0.00"),
                },
                at=timezone.now(),
            )            

    def test_checkout_rejects_order_discounts_exceeding_remaining_amount(self):
        from apps.prices.models import Discount
        from apps.orders.services import create_order_from_cart

        at = timezone.now()

        Discount.objects.create(
            product=self.product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=at,
        )

        order_data = {
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
            "delivery_address_line": "ул. Центральная, 1",
            "delivery_apartment": "10",
            "order_discount": Decimal("181.00"),
            "promotion_discount": Decimal("0.00"),
        }

        with self.assertRaises(ValueError):
            create_order_from_cart(
                cart=self.cart,
                customer=self.user,
                currency=self.currency,
                order_data=order_data,
                at=at,
            )       
