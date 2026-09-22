from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import CustomerAddress
from accounts.serializers import CustomerAddressSerializer


User = get_user_model()


class CustomerAddressSerializerTests(APITestCase):
    def setUp(self):
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

    def test_customer_address_serializer_returns_address_data(self):
        serializer = CustomerAddressSerializer(self.address)
        data = serializer.data

        self.assertEqual(data["id"], self.address.id)
        self.assertEqual(data["title"], "Дом")
        self.assertEqual(data["first_name"], "Иван")
        self.assertEqual(data["last_name"], "Иванов")
        self.assertEqual(data["middle_name"], "Иванович")
        self.assertEqual(data["phone"], "+380501234567")
        self.assertEqual(data["country"], "Украина")
        self.assertEqual(data["region"], "Днепропетровская область")
        self.assertEqual(data["city"], "Днепр")
        self.assertEqual(data["postal_code"], "49000")
        self.assertEqual(data["address_line"], "ул. Центральная, 10")
        self.assertEqual(data["apartment"], "25")
        self.assertTrue(data["is_default"])

    def test_customer_address_read_only_fields(self):
        original_created_at = self.address.created_at
        original_updated_at = self.address.updated_at
        original_pk = self.address.pk

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

        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_address = serializer.save()

        self.assertEqual(updated_address.pk, original_pk)
        self.assertEqual(updated_address.title, "Работа")
        self.assertEqual(updated_address.created_at, original_created_at)
        self.assertGreaterEqual(
            updated_address.updated_at,
            original_updated_at,
        )
