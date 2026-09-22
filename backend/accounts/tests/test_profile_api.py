from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomerProfile


User = get_user_model()


class CustomerProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPassword123!",
        )

        self.profile = CustomerProfile.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
            phone="+380501234567",
        )

    def test_get_customer_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/api/customer/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.profile.pk,
        )
        self.assertEqual(
            response.data["first_name"],
            "Иван",
        )
        self.assertEqual(
            response.data["last_name"],
            "Иванов",
        )
        self.assertEqual(
            response.data["middle_name"],
            "Иванович",
        )
        self.assertEqual(
            response.data["phone"],
            "+380501234567",
        )

    def test_get_customer_profile_anonymous(self):
        response = self.client.get(
            "/api/customer/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_patch_customer_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/customer/profile/",
            {
                "first_name": "Пётр",
                "last_name": "Петров",
                "middle_name": "Петрович",
                "phone": "+380671234567",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.first_name,
            "Пётр",
        )
        self.assertEqual(
            self.profile.last_name,
            "Петров",
        )
        self.assertEqual(
            self.profile.middle_name,
            "Петрович",
        )
        self.assertEqual(
            self.profile.phone,
            "+380671234567",
        )

    def test_patch_customer_profile_read_only_fields(self):
        self.client.force_authenticate(user=self.user)

        original_id = self.profile.pk
        original_created_at = self.profile.created_at
        original_updated_at = self.profile.updated_at

        response = self.client.patch(
            "/api/customer/profile/",
            {
                "id": 999999,
                "first_name": "Пётр",
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.pk,
            original_id,
        )
        self.assertEqual(
            self.profile.first_name,
            "Пётр",
        )
        self.assertEqual(
            self.profile.created_at,
            original_created_at,
        )

        self.assertGreaterEqual(
            self.profile.updated_at,
            original_updated_at,
        )
