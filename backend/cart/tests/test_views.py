from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, CategoryGroup, Group, Product, Type


class CartViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            username="cart-user",
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
            article="TEST-CART-001",
            category=self.category,
            group=self.group,
            type=self.type,
            sales_unit="шт",
            status=True,
        )

    def test_guest_get_creates_cart(self):
        response = self.client.get("/api/cart/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cart.objects.count(), 1)

        cart = Cart.objects.get()

        self.assertIsNone(cart.customer)
        self.assertIsNotNone(cart.session_key)
        self.assertEqual(
            cart.status,
            CartStatus.BUSY,
        )

        self.assertEqual(response.data["id"], cart.id)
        self.assertEqual(response.data["items"], [])

    def test_guest_get_reuses_same_cart(self):
        first_response = self.client.get("/api/cart/")
        second_response = self.client.get("/api/cart/")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"],
        )

    def test_guest_get_reuses_free_cart(self):
        free_cart = Cart.objects.create(
            status=CartStatus.FREE,
        )

        response = self.client.get("/api/cart/")

        self.assertEqual(response.status_code, 200)

        free_cart.refresh_from_db()

        self.assertEqual(response.data["id"], free_cart.id)
        self.assertEqual(free_cart.status, CartStatus.BUSY)
        self.assertIsNone(free_cart.customer)
        self.assertIsNotNone(free_cart.session_key)

        self.assertEqual(Cart.objects.count(), 1)

    def test_authenticated_get_creates_personal_cart(self):
        self.client.force_authenticate(user=self.user)

        first_response = self.client.get("/api/cart/")
        second_response = self.client.get("/api/cart/")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(Cart.objects.count(), 1)

        cart = Cart.objects.get()

        self.assertEqual(cart.customer, self.user)
        self.assertIsNone(cart.session_key)
        self.assertEqual(
            cart.status,
            CartStatus.BUSY,
        )

        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"],
        )
        self.assertEqual(first_response.data["id"], cart.id)

    def test_guest_can_add_item(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)

        item = CartItem.objects.get()

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

        self.assertEqual(
            response.data["product"]["id"],
            self.product.id,
        )
        self.assertEqual(
            response.data["product"]["article"],
            self.product.article,
        )
        self.assertEqual(response.data["quantity"], 2)

    def test_guest_add_existing_item_increases_quantity(self):
        first_response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        second_response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 3,
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)

        item = CartItem.objects.get()

        self.assertEqual(item.quantity, 5)
        self.assertEqual(second_response.data["quantity"], 5)

    #--------
    def test_add_item_rejects_zero_quantity(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_item_rejects_negative_quantity(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": -1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_item_rejects_nonexistent_product(self):
        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": 999999,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_item_rejects_inactive_product(self):
        self.product.status = False
        self.product.save(update_fields=["status"])

        response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)
#--------
    def test_guest_can_delete_cart_item(self):
        add_response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item_id = add_response.data["id"]

        response = self.client.delete(f"/api/cart/items/{item_id}/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(Cart.objects.count(), 1)

    def test_delete_nonexistent_cart_item_returns_404(self):
        response = self.client.delete("/api/cart/items/999999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_guest_cannot_delete_item_from_another_cart(self):
        first_client = APIClient()
        second_client = APIClient()

        first_client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        item = CartItem.objects.get()

        response = second_client.delete(f"/api/cart/items/{item.id}/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(
            CartItem.objects.get().quantity,
            2,
        )

#--------

    def test_guest_can_clear_cart(self):
        first_response = self.client.post(
            "/api/cart/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        cart_id = CartItem.objects.get().cart_id
        item_id = first_response.data["id"]

        response = self.client.delete("/api/cart/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(
            Cart.objects.get().id,
            cart_id,
        )
        self.assertFalse(CartItem.objects.filter(pk=item_id).exists())

    def test_clear_empty_cart_returns_204(self):
        get_response = self.client.get("/api/cart/")

        cart_id = get_response.data["id"]

        response = self.client.delete("/api/cart/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(Cart.objects.get().id, cart_id)
        self.assertEqual(CartItem.objects.count(), 0)