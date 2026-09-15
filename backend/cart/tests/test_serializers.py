from django.contrib.auth import get_user_model
from django.test import TestCase

from cart.models import Cart, CartItem
from cart.serializers import CartItemSerializer, CartSerializer
from catalog.models import (
    Category,
    CategoryGroup,
    Group,
    Product,
    Type,
)


User = get_user_model()


class CartSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="serializer_user",
            password="test-password",
        )

        category = Category.objects.create(
            name="Serializer category",
        )

        group = Group.objects.create(
            name="Serializer group",
        )

        CategoryGroup.objects.create(
            category=category,
            group=group,
        )

        product_type = Type.objects.create(
            name="Serializer type",
        )

        cls.product = Product.objects.create(
            article="SERIALIZER-TEST-001",
            category=category,
            group=group,
            type=product_type,
            sales_unit="шт.",
        )

        cls.cart = Cart.objects.create(
            customer=cls.user,
        )

        cls.item = CartItem.objects.create(
            cart=cls.cart,
            product=cls.product,
            quantity=3,
        )

    def test_cart_item_serialization(self):
        serializer = CartItemSerializer(self.item)

        self.assertEqual(
            serializer.data["product"]["id"],
            self.product.id,
        )
        self.assertEqual(
            serializer.data["product"]["article"],
            self.product.article,
        )
        self.assertEqual(
            serializer.data["quantity"],
            3,
        )

    def test_cart_serialization(self):
        serializer = CartSerializer(self.cart)

        self.assertEqual(
            serializer.data["id"],
            self.cart.id,
        )
        self.assertEqual(
            len(serializer.data["items"]),
            1,
        )

    def test_quantity_zero_is_invalid(self):
        serializer = CartItemSerializer(
            data={
                "product_id": self.product.id,
                "quantity": 0,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_negative_quantity_is_invalid(self):
        serializer = CartItemSerializer(
            data={
                "product_id": self.product.id,
                "quantity": -1,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_valid_quantity_is_valid(self):
        serializer = CartItemSerializer(
            data={
                "product_id": self.product.id,
                "quantity": 5,
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_inactive_product_is_invalid(self):
        self.product.status = False
        self.product.save(update_fields=["status"])

        serializer = CartItemSerializer(
            data={
                "product_id": self.product.id,
                "quantity": 1,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("product_id", serializer.errors)

    def test_cart_owner_fields_are_read_only(self):
        serializer = CartSerializer(
            instance=self.cart,
            data={
                "customer": self.user.id,
                "session_key": "some-session",
                "status": False,
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        self.assertNotIn("customer", serializer.validated_data)
        self.assertNotIn("session_key", serializer.validated_data)
        self.assertNotIn("status", serializer.validated_data)
