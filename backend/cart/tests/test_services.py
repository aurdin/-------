from django.contrib.auth import get_user_model
from django.test import TestCase

from cart.models import Cart, CartItem
from cart.services import (
    merge_guest_cart_with_customer_cart,
    promote_guest_cart_to_customer,
)
from catalog.models import Category, CategoryGroup, Group, Product, Type


class PromoteGuestCartToCustomerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="service-user",
            password="test-password-123",
        )

        self.category = Category.objects.create(
            name="Test category",
        )

        self.group = Group.objects.create(
            name="Test group",
        )

        CategoryGroup.objects.create(
            category=self.category,
            group=self.group,
        )

        self.type = Type.objects.create(
            name="Test type",
        )

        self.product = Product.objects.create(
            article="TEST-SERVICE-001",
            category=self.category,
            group=self.group,
            type=self.type,
            sales_unit="шт",
            status=True,
        )

    def test_guest_cart_becomes_personal_cart(self):
        cart = Cart.objects.create(
            session_key="guest-session-123",
            status=True,
        )

        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=3,
        )

        cart_id = cart.id

        result = promote_guest_cart_to_customer(
            cart,
            self.user,
        )

        result.refresh_from_db()
        item.refresh_from_db()

        self.assertEqual(result.id, cart_id)
        self.assertEqual(result.customer, self.user)
        self.assertIsNone(result.session_key)
        self.assertTrue(result.status)

        self.assertEqual(item.cart_id, cart_id)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 3)

    def test_cannot_promote_personal_cart(self):
        cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Cart already belongs to a customer.",
        ):
            promote_guest_cart_to_customer(
                cart,
                self.user,
            )

    def test_cannot_promote_if_customer_already_has_personal_cart(self):
        Cart.objects.create(
            customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-session-789",
            status=True,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Customer already has a personal cart.",
        ):
            promote_guest_cart_to_customer(
                guest_cart,
                self.user,
            )

        guest_cart.refresh_from_db()

        self.assertIsNone(guest_cart.customer)
        self.assertEqual(
            guest_cart.session_key,
            "guest-session-789",
        )

    def test_merge_same_product_sums_quantities(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-merge-001",
            status=True,
        )

        CartItem.objects.create(
            cart=personal_cart,
            product=self.product,
            quantity=3,
        )

        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=2,
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            self.user,
        )

        result.refresh_from_db()

        item = CartItem.objects.get(
            cart=personal_cart,
            product=self.product,
        )

        self.assertEqual(result.id, personal_cart.id)
        self.assertEqual(item.quantity, 5)
        self.assertFalse(Cart.objects.filter(pk=guest_cart.id).exists())

    def test_merge_moves_product_only_from_guest_cart(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-merge-002",
            status=True,
        )

        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=4,
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            self.user,
        )

        item = CartItem.objects.get(
            cart=personal_cart,
            product=self.product,
        )

        self.assertEqual(result.id, personal_cart.id)
        self.assertEqual(item.quantity, 4)
        self.assertFalse(Cart.objects.filter(pk=guest_cart.id).exists())

    def test_merge_preserves_product_only_in_personal_cart(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-merge-003",
            status=True,
        )

        CartItem.objects.create(
            cart=personal_cart,
            product=self.product,
            quantity=7,
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            self.user,
        )

        item = CartItem.objects.get(
            cart=personal_cart,
            product=self.product,
        )

        self.assertEqual(result.id, personal_cart.id)
        self.assertEqual(item.quantity, 7)
        self.assertFalse(Cart.objects.filter(pk=guest_cart.id).exists())

    def test_merge_deletes_guest_cart(self):
        Cart.objects.create(
        customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-merge-004",
            status=True,
        )

        guest_cart_id = guest_cart.id

        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=2,
        )

        merge_guest_cart_with_customer_cart(
            guest_cart,
            self.user,
        )

        self.assertFalse(Cart.objects.filter(pk=guest_cart_id).exists())
        self.assertEqual(Cart.objects.count(), 1)

    def test_merge_preserves_personal_cart_id(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        guest_cart = Cart.objects.create(
            session_key="guest-merge-005",
            status=True,
        )

        personal_cart_id = personal_cart.id

        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=2,
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            self.user,
        )

        self.assertEqual(result.id, personal_cart_id)
        self.assertTrue(
            Cart.objects.filter(
                pk=personal_cart_id,
                customer=self.user,
            ).exists()
        )
# -------------------------
    def test_merge_rejects_personal_cart(self):
        personal_cart = Cart.objects.create(
            customer=self.user,
            status=True,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Cart already belongs to a customer.",
        ):
            merge_guest_cart_with_customer_cart(
                personal_cart,
                self.user,
            )

    def test_merge_rejects_customer_without_personal_cart(self):
        guest_cart = Cart.objects.create(
            session_key="guest-merge-error-001",
            status=True,
        )

        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=3,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Customer does not have a personal cart.",
        ):
            merge_guest_cart_with_customer_cart(
                guest_cart,
                self.user,
            )

        guest_cart.refresh_from_db()

        self.assertIsNone(guest_cart.customer)
        self.assertEqual(
            guest_cart.session_key,
            "guest-merge-error-001",
        )

        item = CartItem.objects.get(cart=guest_cart)

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 3)

    def test_merge_error_does_not_delete_guest_cart(self):
        guest_cart = Cart.objects.create(
            session_key="guest-merge-error-002",
            status=True,
        )

        guest_cart_id = guest_cart.id

        with self.assertRaisesMessage(
            ValueError,
            "Customer does not have a personal cart.",
        ):
            merge_guest_cart_with_customer_cart(
                guest_cart,
                self.user,
            )

        self.assertTrue(Cart.objects.filter(pk=guest_cart_id).exists())
# --------------------------


