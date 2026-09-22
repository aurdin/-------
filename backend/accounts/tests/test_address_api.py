from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomerAddress


User = get_user_model()


class CustomerAddressAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="addressuser",
            email="address@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPassword123!",
        )

    def test_list_customer_addresses_authenticated(self):
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
            user=self.other_user,
            title="Другой адрес",
            first_name="Пётр",
            last_name="Петров",
            phone="+380671234567",
            country="Украина",
            city="Киев",
            address_line="ул. Крещатик, 1",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/customer/addresses/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Дом")

    def test_list_customer_addresses_anonymous(self):
        response = self.client.get("/api/customer/addresses/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_customer_address_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/customer/addresses/",
            {
                "title": "Дом",
                "first_name": "Иван",
                "last_name": "Иванов",
                "middle_name": "Иванович",
                "phone": "+380501234567",
                "country": "Украина",
                "region": "Днепропетровская область",
                "city": "Днепр",
                "postal_code": "49000",
                "address_line": "ул. Центральная, 10",
                "apartment": "25",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        address = CustomerAddress.objects.get(pk=response.data["id"])

        self.assertEqual(address.user, self.user)
        self.assertEqual(address.title, "Дом")
        self.assertEqual(address.city, "Днепр")

    def test_create_customer_address_anonymous(self):
        response = self.client.post(
            "/api/customer/addresses/",
            {
                "title": "Дом",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+380501234567",
                "country": "Украина",
                "city": "Днепр",
                "address_line": "ул. Центральная, 10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_default_address_removes_previous_default(self):
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

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/customer/addresses/",
            {
                "title": "Работа",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+380501234567",
                "country": "Украина",
                "city": "Днепр",
                "address_line": "ул. Рабочая, 20",
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        first_address.refresh_from_db()
        second_address = CustomerAddress.objects.get(pk=response.data["id"])

        self.assertFalse(first_address.is_default)
        self.assertTrue(second_address.is_default)

        self.assertEqual(
            CustomerAddress.objects.filter(
                user=self.user,
                is_default=True,
            ).count(),
            1,
        )

    def test_create_address_for_one_user_does_not_affect_other_user(self):
        other_address = CustomerAddress.objects.create(
            user=self.other_user,
            title="Другой адрес",
            first_name="Пётр",
            last_name="Петров",
            phone="+380671234567",
            country="Украина",
            city="Киев",
            address_line="ул. Крещатик, 1",
            is_default=True,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/customer/addresses/",
            {
                "title": "Дом",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+380501234567",
                "country": "Украина",
                "city": "Днепр",
                "address_line": "ул. Центральная, 10",
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        other_address.refresh_from_db()

        self.assertTrue(other_address.is_default)
