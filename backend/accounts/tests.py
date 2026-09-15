from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class RegisterTests(APITestCase):
    def test_register_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(User.objects.filter(username="testuser").exists())

        user = User.objects.get(username="testuser")

        self.assertEqual(
            user.email,
            "test@example.com",
        )

        self.assertTrue(user.check_password("StrongPassword123!"))

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

    def test_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "testuser",
        )

        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_wrong_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class CurrentUserTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "testuser",
        )

    def test_me_anonymous(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPassword123!",
        )

    def test_logout(self):
        self.client.login(
            username="testuser",
            password="StrongPassword123!",
        )

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )