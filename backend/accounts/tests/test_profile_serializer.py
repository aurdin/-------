from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import CustomerProfile
from accounts.serializers import CustomerProfileSerializer


User = get_user_model()


class CustomerProfileSerializerTests(APITestCase):
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

    def test_customer_profile_serializer_returns_profile_data(self):
        serializer = CustomerProfileSerializer(self.profile)

        self.assertEqual(
            serializer.data["first_name"],
            "Иван",
        )
        self.assertEqual(
            serializer.data["last_name"],
            "Иванов",
        )
        self.assertEqual(
            serializer.data["middle_name"],
            "Иванович",
        )
        self.assertEqual(
            serializer.data["phone"],
            "+380501234567",
        )

    def test_customer_profile_read_only_fields(self):
        serializer = CustomerProfileSerializer(
            self.profile,
            data={
                "id": 9999,
                "first_name": "Пётр",
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

        serializer.save()

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.first_name,
            "Пётр",
        )
        self.assertNotEqual(
            self.profile.pk,
            9999,
        )
