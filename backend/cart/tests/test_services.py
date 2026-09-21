from django.contrib.auth import get_user_model
from django.test import TestCase

from cart.models import Cart, CartItem, CartStatus
from cart.services import (
    attach_guest_cart_to_customer,
    merge_guest_cart_with_customer_cart,
    promote_guest_cart_to_customer,
)
from catalog.models import (
    Category,
    CategoryGroup,
    Group,
    Product,
    Type,
)


User = get_user_model()


class CartServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # --------------------------------------------------------------
        # Catalog test data
        # --------------------------------------------------------------

        cls.category = Category.objects.create(
            name="Тестовая категория",
        )

        cls.group = Group.objects.create(
            name="Тестовая группа",
        )

        CategoryGroup.objects.create(
            category=cls.category,
            group=cls.group,
        )

        cls.type_1 = Type.objects.create(
            name="Тестовый тип",
        )

        cls.type_2 = Type.objects.create(
            name="Тестовый тип 2",
        )

        cls.product_1 = Product.objects.create(
            article="TEST-CART-001",
            category=cls.category,
            group=cls.group,
            type=cls.type_1,
            sales_unit="шт.",
        )

        cls.product_2 = Product.objects.create(
            article="TEST-CART-002",
            category=cls.category,
            group=cls.group,
            type=cls.type_2,
            sales_unit="шт.",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            password="testpassword123",
        )

    def create_guest_cart(self, session_key):
        return Cart.objects.create(
            session_key=session_key,
            status=CartStatus.BUSY,
        )

    def create_customer_cart(self, customer):
        return Cart.objects.create(
            customer=customer,
            status=CartStatus.BUSY,
        )

    def add_item(self, cart, product, quantity):
        return CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )

    # ------------------------------------------------------------------
    # promote_guest_cart_to_customer
    # ------------------------------------------------------------------

    def test_promote_guest_cart_to_customer(self):
        customer = self.create_user(
            "promote-user-001",
        )

        guest_cart = self.create_guest_cart(
            "promote-session-001",
        )

        self.add_item(
            guest_cart,
            self.product_1,
            3,
        )

        result = promote_guest_cart_to_customer(
            guest_cart,
            customer,
        )

        guest_cart.refresh_from_db()

        self.assertEqual(
            result.pk,
            guest_cart.pk,
        )

        self.assertEqual(
            guest_cart.customer,
            customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertEqual(
            guest_cart.status,
            CartStatus.BUSY,
        )

        self.assertTrue(
            CartItem.objects.filter(
                cart=guest_cart,
                product=self.product_1,
                quantity=3,
            ).exists()
        )

    def test_promote_empty_guest_cart_to_customer(self):
        customer = self.create_user(
            "promote-user-002",
        )

        guest_cart = self.create_guest_cart(
            "promote-session-002",
        )

        result = promote_guest_cart_to_customer(
            guest_cart,
            customer,
        )

        guest_cart.refresh_from_db()

        self.assertEqual(
            result.pk,
            guest_cart.pk,
        )

        self.assertEqual(
            guest_cart.customer,
            customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertEqual(
            guest_cart.status,
            CartStatus.BUSY,
        )

    def test_promote_cart_already_belongs_to_customer_raises_error(self):
        customer_1 = self.create_user(
            "promote-user-003",
        )

        customer_2 = self.create_user(
            "promote-user-004",
        )

        cart = self.create_customer_cart(
            customer_1,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Cart already belongs to a customer.",
        ):
            promote_guest_cart_to_customer(
                cart,
                customer_2,
            )

    def test_promote_cart_without_session_key_raises_error(self):
        customer = self.create_user(
            "promote-user-005",
        )

        cart = self.create_guest_cart(
            "promote-session-005",
        )

        cart.session_key = None

        with self.assertRaisesMessage(
            ValueError,
            "Cart is not a guest cart.",
        ):
            promote_guest_cart_to_customer(
                cart,
                customer,
            )   

    def test_promote_when_customer_already_has_cart_raises_error(self):
        customer = self.create_user(
            "promote-user-006",
        )

        self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "promote-session-006",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Customer already has a personal cart.",
        ):
            promote_guest_cart_to_customer(
                guest_cart,
                customer,
            )

    # ------------------------------------------------------------------
    # merge_guest_cart_with_customer_cart
    # ------------------------------------------------------------------

    def test_merge_guest_cart_into_customer_cart(self):
        customer = self.create_user(
            "merge-user-001",
        )

        personal_cart = self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "merge-session-001",
        )

        self.add_item(
            guest_cart,
            self.product_1,
            2,
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            customer,
        )

        personal_cart.refresh_from_db()
        guest_cart.refresh_from_db()

        self.assertEqual(
            result.pk,
            personal_cart.pk,
        )

        item = CartItem.objects.get(
            cart=personal_cart,
            product=self.product_1,
        )

        self.assertEqual(
            item.quantity,
            2,
        )

        self.assertEqual(
            guest_cart.items.count(),
            0,
        )

        self.assertIsNone(
            guest_cart.customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertEqual(
            guest_cart.status,
            CartStatus.FREE,
        )

    def test_merge_same_product_adds_quantities(self):
        customer = self.create_user(
            "merge-user-002",
        )

        personal_cart = self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "merge-session-002",
        )

        self.add_item(
            personal_cart,
            self.product_1,
            5,
        )

        self.add_item(
            guest_cart,
            self.product_1,
            3,
        )

        merge_guest_cart_with_customer_cart(
            guest_cart,
            customer,
        )

        item = CartItem.objects.get(
            cart=personal_cart,
            product=self.product_1,
        )

        self.assertEqual(
            item.quantity,
            8,
        )

        self.assertEqual(
            CartItem.objects.filter(
                cart=personal_cart,
                product=self.product_1,
            ).count(),
            1,
        )

    def test_merge_different_products_moves_all_items(self):
        customer = self.create_user(
            "merge-user-003",
        )

        personal_cart = self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "merge-session-003",
        )

        self.add_item(
            personal_cart,
            self.product_1,
            2,
        )

        self.add_item(
            guest_cart,
            self.product_2,
            7,
        )

        merge_guest_cart_with_customer_cart(
            guest_cart,
            customer,
        )

        self.assertTrue(
            CartItem.objects.filter(
                cart=personal_cart,
                product=self.product_1,
                quantity=2,
            ).exists()
        )

        self.assertTrue(
            CartItem.objects.filter(
                cart=personal_cart,
                product=self.product_2,
                quantity=7,
            ).exists()
        )

        self.assertEqual(
            guest_cart.items.count(),
            0,
        )

    def test_merge_empty_guest_cart(self):
        customer = self.create_user(
            "merge-user-004",
        )

        personal_cart = self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "merge-session-004",
        )

        result = merge_guest_cart_with_customer_cart(
            guest_cart,
            customer,
        )

        self.assertEqual(
            result.pk,
            personal_cart.pk,
        )

        guest_cart.refresh_from_db()

        self.assertIsNone(
            guest_cart.customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertEqual(
            guest_cart.status,
            CartStatus.FREE,
        )

    def test_merge_cart_already_belongs_to_customer_raises_error(self):
        customer = self.create_user(
            "merge-user-005",
        )

        self.create_customer_cart(
            customer,
        )

        other_customer = self.create_user(
            "merge-other-user-005",
        )

        guest_cart = self.create_customer_cart(
            other_customer,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Cart already belongs to a customer.",
        ):
            merge_guest_cart_with_customer_cart(
                guest_cart,
                customer,
            )

    def test_merge_cart_without_session_key_raises_error(self):
        customer = self.create_user(
            "merge-user-006",
        )

        self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "merge-session-006",
        )

        guest_cart.session_key = None

        with self.assertRaisesMessage(
            ValueError,
            "Cart is not a guest cart.",
        ):
            merge_guest_cart_with_customer_cart(
                guest_cart,
                customer,
            )

    def test_merge_when_customer_has_no_personal_cart_raises_error(self):
        customer = self.create_user(
            "merge-user-007",
        )

        guest_cart = self.create_guest_cart(
            "merge-session-007",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Customer does not have a personal cart.",
        ):
            merge_guest_cart_with_customer_cart(
                guest_cart,
                customer,
            )

    # ------------------------------------------------------------------
    # attach_guest_cart_to_customer
    # ------------------------------------------------------------------

    def test_attach_without_session_key_creates_customer_cart(self):
        customer = self.create_user(
            "attach-user-001",
        )

        result = attach_guest_cart_to_customer(
            None,
            customer,
        )

        self.assertEqual(
            result.customer,
            customer,
        )

        self.assertEqual(
            result.status,
            CartStatus.BUSY,
        )

    def test_attach_empty_session_key_creates_customer_cart(self):
        customer = self.create_user(
            "attach-user-002",
        )

        result = attach_guest_cart_to_customer(
            "",
            customer,
        )

        self.assertEqual(
            result.customer,
            customer,
        )

        self.assertEqual(
            result.status,
            CartStatus.BUSY,
        )

    def test_attach_guest_cart_promotes_it_when_customer_has_no_cart(self):
        customer = self.create_user(
            "attach-user-003",
        )

        guest_cart = self.create_guest_cart(
            "attach-session-003",
        )

        self.add_item(
            guest_cart,
            self.product_1,
            4,
        )

        result = attach_guest_cart_to_customer(
            "attach-session-003",
            customer,
        )

        guest_cart.refresh_from_db()

        self.assertEqual(
            result.pk,
            guest_cart.pk,
        )

        self.assertEqual(
            guest_cart.customer,
            customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertTrue(
            CartItem.objects.filter(
                cart=guest_cart,
                product=self.product_1,
                quantity=4,
            ).exists()
        )

    def test_attach_guest_cart_merges_when_customer_already_has_cart(self):
        customer = self.create_user(
            "attach-user-004",
        )

        personal_cart = self.create_customer_cart(
            customer,
        )

        guest_cart = self.create_guest_cart(
            "attach-session-004",
        )

        self.add_item(
            personal_cart,
            self.product_1,
            2,
        )

        self.add_item(
            guest_cart,
            self.product_1,
            3,
        )

        self.add_item(
            guest_cart,
            self.product_2,
            5,
        )

        result = attach_guest_cart_to_customer(
            "attach-session-004",
            customer,
        )

        personal_cart.refresh_from_db()
        guest_cart.refresh_from_db()

        self.assertEqual(
            result.pk,
            personal_cart.pk,
        )

        item_1 = CartItem.objects.get(
            cart=personal_cart,
            product=self.product_1,
        )

        item_2 = CartItem.objects.get(
            cart=personal_cart,
            product=self.product_2,
        )

        self.assertEqual(
            item_1.quantity,
            5,
        )

        self.assertEqual(
            item_2.quantity,
            5,
        )

        self.assertEqual(
            guest_cart.items.count(),
            0,
        )

        self.assertIsNone(
            guest_cart.customer,
        )

        self.assertIsNone(
            guest_cart.session_key,
        )

        self.assertEqual(
            guest_cart.status,
            CartStatus.FREE,
        )

    def test_attach_unknown_session_creates_customer_cart(self):
        customer = self.create_user(
            "attach-user-005",
        )

        result = attach_guest_cart_to_customer(
            "unknown-session-005",
            customer,
        )

        self.assertEqual(
            result.customer,
            customer,
        )

        self.assertEqual(
            result.status,
            CartStatus.BUSY,
        )

    def test_attach_existing_guest_cart_does_not_create_second_cart(self):
        customer = self.create_user(
            "attach-user-006",
        )

        guest_cart = self.create_guest_cart(
            "attach-session-006",
        )

        result = attach_guest_cart_to_customer(
            "attach-session-006",
            customer,
        )

        self.assertEqual(
            Cart.objects.filter(
                customer=customer,
            ).count(),
            1,
        )

        self.assertEqual(
            result.pk,
            guest_cart.pk,
        )

    def test_attach_without_session_returns_existing_customer_cart(self):
        customer = self.create_user(
            "attach-user-007",
        )

        existing_cart = self.create_customer_cart(
            customer,
        )

        result = attach_guest_cart_to_customer(
            None,
            customer,
        )

        self.assertEqual(
            result.pk,
            existing_cart.pk,
        )

        self.assertEqual(
            Cart.objects.filter(
                customer=customer,
            ).count(),
            1,
        )
