from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomerProfile, CustomerAddress


User = get_user_model()


class RegisterTests(APITestCase): # Регистрация тестов пользователей
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

    def test_register_password_mismatch(self): # Тест на несовпадение паролей при регистрации
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
# ------------------------
    def test_register_creates_customer_profile(self): # Тест на создание профиля клиента при регистрации
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "profileuser",
                "email": "profile@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(username="profileuser")

        self.assertTrue(
            hasattr(user, "customer_profile"),
        )

        self.assertEqual(
            user.customer_profile.user,
            user,
        )

class LoginTests(APITestCase): # Тесты входа в систему
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

    def test_login(self): # Тест входа в систему
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

    def test_login_wrong_password(self): # Тест входа с неправильным паролем
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


class CurrentUserTests(APITestCase): # Тесты текущего пользователя
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

    def test_me_authenticated(self): # Тест получения информации о текущем пользователе
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

    def test_me_anonymous(self): # Тест получения информации о анонимном пользователе
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class LogoutTests(APITestCase): # Тесты выхода из системы

    def setUp(self): # Настройка теста выхода из системы
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPassword123!",
        )

    def test_logout(self): # Тест выхода из системы
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
# ------------------------
class CustomerProfileModelTests(APITestCase): # Тесты модели профиля клиента

    def test_customer_profile_can_be_created(self): # Тест на создание профиля клиента
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

    def test_customer_profile_has_one_to_one_user_relation(self): # Тест на наличие отношения "один к одному" с моделью пользователя
        user = User.objects.create_user(
            username="profileuser",
            password="StrongPassword123!",
        )

        profile = CustomerProfile.objects.create(
            user=user,
        )

        self.assertEqual(user.customer_profile, profile)

    def test_customer_profile_optional_fields_can_be_empty(self): # Тест на пустые опциональные поля профиля клиента
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

    def test_customer_profile_str(self): # Тест строкового представления профиля клиента
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
# ------------------------
class CustomerProfileSerializerTests(APITestCase): # Тесты сериализатора профиля клиента

    def setUp(self): # Настройка теста сериализатора профиля клиента
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

    def test_customer_profile_serializer_returns_profile_data(self): # Тест на возврат данных профиля клиента сериализатором
        from accounts.serializers import CustomerProfileSerializer

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

    def test_customer_profile_read_only_fields(self): # Тест на проверку полей только для чтения в сериализаторе профиля клиента
        from accounts.serializers import CustomerProfileSerializer

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
# ------------------------
class CustomerProfileAPITests(APITestCase): # Тесты API профиля клиента

    def setUp(self): # Настройка теста API профиля клиента
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

    def test_get_customer_profile_authenticated(self): # Тест получения профиля клиента для аутентифицированного пользователя
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

    def test_get_customer_profile_anonymous(self): # Тест получения профиля клиента для анонимного пользователя
        response = self.client.get(
            "/api/customer/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_patch_customer_profile_authenticated(self): # Тест обновления профиля клиента для аутентифицированного пользователя
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

    def test_patch_customer_profile_read_only_fields(self): # Тест на проверку полей только для чтения при обновлении профиля клиента
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
# ------------------------
class CustomerAddressModelTests(APITestCase): # Тесты модели адреса клиента

    def setUp(self): # Настройка теста модели адреса клиента
        self.user = User.objects.create_user(
            username="addressuser",
            email="address@example.com",
            password="StrongPassword123!",
        )

    def test_customer_address_can_be_created(self): # Тест на создание адреса клиента
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

    def test_customer_address_optional_fields_can_be_empty(self): # Тест на проверку пустых опциональных полей адреса клиента
        address = CustomerAddress.objects.create(
            user=self.user,
            first_name="Иван",
            last_name="Иванов",
            phone="+380501234567",
            country="Украина",
            city="Днепр",
            address_line="ул. Центральная, 10",
        )

        self.assertEqual(address.title, "")
        self.assertEqual(address.middle_name, "")
        self.assertEqual(address.region, "")
        self.assertEqual(address.postal_code, "")
        self.assertEqual(address.apartment, "")

    def test_customer_can_have_multiple_addresses(self): # Тест на проверку возможности иметь несколько адресов
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
            CustomerAddress.objects.filter(user=self.user).count(),
            2,
        )

    def test_only_one_default_address_is_allowed(self): # Тест на проверку возможности иметь только один адрес по умолчанию
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

        self.assertTrue(first_address.is_default)

    def test_customer_address_str_with_title(self): # Тест на строковое представление адреса клиента с заголовком
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

    def test_customer_address_str_without_title(self):  # Тест на строковое представление адреса клиента без заголовка
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
# ------------------------
class CustomerAddressSerializerTests(APITestCase): # Тесты сериализатора адреса клиента

    def setUp(self): # Настройка теста сериализатора адреса клиента
        self.user = User.objects.create_user(
            username="addressuser",
            email="address@example.com",
            password="StrongPassword123!",
        )

        self.address = CustomerAddress.objects.create(
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
            is_default=True,
        )

    def test_customer_address_serializer_returns_address_data(self): # Тест на возврат данных адреса клиента сериализатором
        from accounts.serializers import CustomerAddressSerializer

        serializer = CustomerAddressSerializer(self.address)

        self.assertEqual(
            serializer.data["id"],
            self.address.pk,
        )
        self.assertEqual(
            serializer.data["title"],
            "Дом",
        )
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
        self.assertEqual(
            serializer.data["country"],
            "Украина",
        )
        self.assertEqual(
            serializer.data["region"],
            "Днепропетровская область",
        )
        self.assertEqual(
            serializer.data["city"],
            "Днепр",
        )
        self.assertEqual(
            serializer.data["postal_code"],
            "49000",
        )
        self.assertEqual(
            serializer.data["address_line"],
            "ул. Центральная, 10",
        )
        self.assertEqual(
            serializer.data["apartment"],
            "25",
        )
        self.assertTrue(
            serializer.data["is_default"],
        )

    def test_customer_address_read_only_fields(self): # Тест на проверку полей только для чтения в сериализаторе адреса клиента
        from accounts.serializers import CustomerAddressSerializer

        original_id = self.address.pk
        original_created_at = self.address.created_at
        original_updated_at = self.address.updated_at

        serializer = CustomerAddressSerializer(
            self.address,
            data={
                "id": 999999,
                "title": "Работа",
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
        )

        serializer.save()

        self.address.refresh_from_db()

        self.assertEqual(
            self.address.pk,
            original_id,
        )
        self.assertEqual(
            self.address.title,
            "Работа",
        )
        self.assertEqual(
            self.address.created_at,
            original_created_at,
        )
        self.assertGreaterEqual(
            self.address.updated_at,
            original_updated_at,
        )
# ------------------------
class CustomerAddressAPITests(APITestCase): # Тесты API адреса клиента

    def setUp(self): # Настройка теста API адреса клиента
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

    def test_list_customer_addresses_authenticated(self): # Тест на список адресов клиента при аутентификации
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
            address_line="ул. Киевская, 20",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/customer/addresses/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["title"],
            "Дом",
        )

    def test_list_customer_addresses_anonymous(self): # Тест на список адресов клиента при анонимном доступе
        response = self.client.get(
            "/api/customer/addresses/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_customer_address_authenticated(self): # Тест на создание адреса клиента при аутентификации
        self.client.force_authenticate(
            user=self.user,
        )

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
                "is_default": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        address = CustomerAddress.objects.get(
            pk=response.data["id"],
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

    def test_create_customer_address_anonymous(self): # Тест на создание адреса клиента при анонимном доступе
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

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_default_address_removes_previous_default(self): # Тест на удаление предыдущего адреса по умолчанию при создании нового
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

        self.client.force_authenticate(
            user=self.user,
        )

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

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        first_address.refresh_from_db()

        second_address = CustomerAddress.objects.get(
            pk=response.data["id"],
        )

        self.assertFalse(
            first_address.is_default,
        )
        self.assertTrue(
            second_address.is_default,
        )

        self.assertEqual(
            CustomerAddress.objects.filter(
                user=self.user,
                is_default=True,
            ).count(),
            1,
        )

    def test_create_address_for_one_user_does_not_affect_other_user(self): # Тест на проверку того, что создание адреса для одного пользователя не влияет на других пользователей
        other_address = CustomerAddress.objects.create(
            user=self.other_user,
            title="Другой адрес",
            first_name="Пётр",
            last_name="Петров",
            phone="+380671234567",
            country="Украина",
            city="Киев",
            address_line="ул. Киевская, 20",
            is_default=True,
        )

        self.client.force_authenticate(
            user=self.user,
        )

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

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        other_address.refresh_from_db()

        self.assertTrue(
            other_address.is_default,
        )  
# ------------------------
class CustomerAddressDetailAPITests(APITestCase): # Тесты детального представления адреса клиента

    def setUp(self): # Настройка тестов
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
            middle_name="Иванович",
            phone="+380501234567",
            country="Украина",
            region="Днепропетровская область",
            city="Днепр",
            postal_code="49000",
            address_line="ул. Центральная, 10",
            apartment="25",
            is_default=True,
        )

        self.other_address = CustomerAddress.objects.create(
            user=self.other_user,
            title="Работа",
            first_name="Пётр",
            last_name="Петров",
            phone="+380671234567",
            country="Украина",
            city="Киев",
            address_line="ул. Киевская, 20",
            is_default=True,
        )

    def test_get_own_address(self): # Тест 
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            f"/api/customer/addresses/{self.address.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.address.pk,
        )
        self.assertEqual(
            response.data["title"],
            "Дом",
        )

    def test_get_other_user_address_returns_404(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            f"/api/customer/addresses/{self.other_address.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_get_address_anonymous(self):
        response = self.client.get(
            f"/api/customer/addresses/{self.address.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_patch_own_address(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            f"/api/customer/addresses/{self.address.pk}/",
            {
                "title": "Новый дом",
                "city": "Запорожье",
                "apartment": "50",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.address.refresh_from_db()

        self.assertEqual(
            self.address.title,
            "Новый дом",
        )
        self.assertEqual(
            self.address.city,
            "Запорожье",
        )
        self.assertEqual(
            self.address.apartment,
            "50",
        )

    def test_patch_other_user_address_returns_404(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            f"/api/customer/addresses/{self.other_address.pk}/",
            {
                "city": "Одесса",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_address.refresh_from_db()

        self.assertEqual(
            self.other_address.city,
            "Киев",
        )

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

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            f"/api/customer/addresses/{second_address.pk}/",
            {
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.address.refresh_from_db()
        second_address.refresh_from_db()

        self.assertFalse(
            self.address.is_default,
        )
        self.assertTrue(
            second_address.is_default,
        )

        self.assertEqual(
            CustomerAddress.objects.filter(
                user=self.user,
                is_default=True,
            ).count(),
            1,
        )

    def test_delete_own_address(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.delete(
            f"/api/customer/addresses/{self.address.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            CustomerAddress.objects.filter(
                pk=self.address.pk,
            ).exists(),
        )

    def test_delete_other_user_address_returns_404(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.delete(
            f"/api/customer/addresses/{self.other_address.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            CustomerAddress.objects.filter(
                pk=self.other_address.pk,
            ).exists(),
        )           