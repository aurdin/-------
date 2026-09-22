from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import CustomerAddress


User = get_user_model()


class CustomerAddressModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="addressuser",
            email="address@example.com",
            password="StrongPassword123!",
        )

    def test_customer_address_can_be_created(self):
        address = CustomerAddress.objects.create(
            user=self.user,
            title="Дом",
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
            phone="+380501234567",
            country="Украина",
            region="Днепропетровская область",
            city="Днепр",
            postal_code="49000",
            address_line="ул. Центральная, 10",
            apartment="25",
        )

        self.assertEqual(
            address.user,
            self.user,
        )
        self.assertEqual(
            address.title,
            "Дом",
        )
        self.assertEqual(
            address.city,
            "Днепр",
        )
        self.assertFalse(
            address.is_default,
        )

    def test_customer_address_optional_fields_can_be_empty(self):
        address = CustomerAddress.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
        )

        self.assertEqual(
            address.title,
            "",
        )
        self.assertEqual(
            address.middle_name,
            "",
        )
        self.assertEqual(
            address.region,
            "",
        )
        self.assertEqual(
            address.postal_code,
            "",
        )
        self.assertEqual(
            address.apartment,
            "",
        )

    def test_customer_can_have_multiple_addresses(self):
        CustomerAddress.objects.create(
            user=self.user,
            title="Дом",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
        )

        CustomerAddress.objects.create(
            user=self.user,
            title="Работа",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Рабочая, 20",
        )

        self.assertEqual(
            CustomerAddress.objects.filter(
                user=self.user,
            ).count(),
            2,
        )

    def test_only_one_default_address_is_allowed(self):
        first_address = CustomerAddress.objects.create(
            user=self.user,
            title="Дом",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
            is_default=True,
        )

        second_address = CustomerAddress(
            user=self.user,
            title="Работа",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Рабочая, 20",
            is_default=True,
        )

        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            second_address.save()

        self.assertTrue(
            first_address.is_default,
        )

    def test_customer_address_str_with_title(self):
        address = CustomerAddress.objects.create(
            user=self.user,
            title="Дом",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
        )

        self.assertEqual(
            str(address),
            "Дом — addressuser",
        )

    def test_customer_address_str_without_title(self):
        address = CustomerAddress.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
        )

        self.assertEqual(
            str(address),
            f"CustomerAddress #{address.pk} — addressuser",
        )
