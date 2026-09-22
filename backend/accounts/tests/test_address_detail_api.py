from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomerAddress


User = get_user_model()


class CustomerAddressDetailAPITests(APITestCase):
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

        self.address = CustomerAddress.objects.create(
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

        self.other_address = CustomerAddress.objects.create(
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

    def test_get_own_address(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/api/customer/addresses/{self.address.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.address.pk)
        self.assertEqual(response.data["title"], "Дом")

    def test_get_other_user_address_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/api/customer/addresses/{self.other_address.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_address_anonymous(self):
        response = self.client.get(f"/api/customer/addresses/{self.address.pk}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_own_address(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/customer/addresses/{self.address.pk}/",
            {
                "title": "Работа",
                "city": "Киев",
                "apartment": "101",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.address.refresh_from_db()

        self.assertEqual(self.address.title, "Работа")
        self.assertEqual(self.address.city, "Киев")
        self.assertEqual(self.address.apartment, "101")

    def test_patch_other_user_address_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/customer/addresses/{self.other_address.pk}/",
            {
                "city": "Львов",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.other_address.refresh_from_db()

        self.assertEqual(self.other_address.city, "Киев")

    def test_patch_address_as_default_removes_previous_default(self):
        second_address = CustomerAddress.objects.create(
            user=self.user,
            title="Работа",
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Рабочая, 20",
            is_default=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/customer/addresses/{second_address.pk}/",
            {
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.address.refresh_from_db()
        second_address.refresh_from_db()

        self.assertFalse(self.address.is_default)
        self.assertTrue(second_address.is_default)

        self.assertEqual(
            CustomerAddress.objects.filter(
                user=self.user,
                is_default=True,
            ).count(),
            1,
        )

    def test_delete_own_address(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f"/api/customer/addresses/{self.address.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(CustomerAddress.objects.filter(pk=self.address.pk).exists())

    def test_delete_other_user_address_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            f"/api/customer/addresses/{self.other_address.pk}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(
            CustomerAddress.objects.filter(pk=self.other_address.pk).exists()
        )
