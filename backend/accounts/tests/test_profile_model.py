from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import CustomerProfile


User = get_user_model()


class CustomerProfileModelTests(APITestCase):
    def test_customer_profile_can_be_created(self):
        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPassword123!",
        )

        profile = CustomerProfile.objects.create(
            user=user,
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
            phone="+380501234567",
        )

        self.assertEqual(profile.user, user)
        self.assertEqual(profile.first_name, "Иван")
        self.assertEqual(profile.last_name, "Иванов")
        self.assertEqual(profile.middle_name, "Иванович")
        self.assertEqual(profile.phone, "+380501234567")

    def test_customer_profile_has_one_to_one_user_relation(self):
        user = User.objects.create_user(
            username="profileuser",
            password="StrongPassword123!",
        )

        profile = CustomerProfile.objects.create(
            user=user,
        )

        self.assertEqual(user.customer_profile, profile)

    def test_customer_profile_optional_fields_can_be_empty(self):
        user = User.objects.create_user(
            username="profileuser",
            password="StrongPassword123!",
        )

        profile = CustomerProfile.objects.create(
            user=user,
        )

        self.assertEqual(profile.first_name, "")
        self.assertEqual(profile.last_name, "")
        self.assertEqual(profile.middle_name, "")
        self.assertEqual(profile.phone, "")

    def test_customer_profile_str(self):
        user = User.objects.create_user(
            username="profileuser",
            password="StrongPassword123!",
        )

        profile = CustomerProfile.objects.create(
            user=user,
        )

        self.assertEqual(
            str(profile),
            f"CustomerProfile #{profile.pk} — profileuser",
        )
