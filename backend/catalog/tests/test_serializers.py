from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Characteristic,
    Color,
    Execution,
    Group,
    Model,
    Product,
    ProductCharacteristic,
    Series,
    Type,
)
from catalog.serializers import ProductSerializer


class ProductSerializerTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Для дома",
        )

        self.group = Group.objects.create(
            name="Розетки",
        )

        self.brand = Brand.objects.create(
            name="Legrand",
        )

        self.type = Type.objects.create(
            name="Розетка",
        )

        self.model = Model.objects.create(
            name="Valena",
            type=self.type,
        )

        self.execution = Execution.objects.create(
            name="С заземлением",
            type=self.type,
        )

        self.series = Series.objects.create(
            name="Life",
            brand=self.brand,
        )

        self.color = Color.objects.create(
            name="Белый",
        )

    def create_product(self, **kwargs):
        defaults = {
            "article": "TEST-001",
            "category": self.category,
            "group": self.group,
            "brand": self.brand,
            "series": self.series,
            "type": self.type,
            "model": self.model,
            "execution": self.execution,
            "color": self.color,
            "protection_degree": "IP44",
            "packaging": "1 шт.",
            "sales_unit": "шт.",
            "barcode": "1234567890123",
        }

        defaults.update(kwargs)

        product = Product(**defaults)
        product.full_clean()
        product.save()

        return product

    def test_product_serializer_returns_basic_fields(self):
        product = self.create_product()

        data = ProductSerializer(product).data

        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["article"], "TEST-001")
        self.assertEqual(
            data["name"],
            "Розетка Valena С заземлением IP44 Legrand Life Белый",
        )

    def test_product_serializer_returns_references(self):
        product = self.create_product()

        data = ProductSerializer(product).data

        self.assertEqual(
            data["category"],
            {
                "id": self.category.id,
                "name": "Для дома",
            },
        )

        self.assertEqual(
            data["group"],
            {
                "id": self.group.id,
                "name": "Розетки",
            },
        )

        self.assertEqual(
            data["brand"],
            {
                "id": self.brand.id,
                "name": "Legrand",
            },
        )

        self.assertEqual(
            data["series"],
            {
                "id": self.series.id,
                "name": "Life",
            },
        )

        self.assertEqual(
            data["type"],
            {
                "id": self.type.id,
                "name": "Розетка",
            },
        )

    def test_product_serializer_returns_standard_fields(self):
        product = self.create_product()

        data = ProductSerializer(product).data

        self.assertEqual(data["protection_degree"], "IP44")
        self.assertEqual(
            data["color"],
            {
                "id": self.color.id,
                "name": "Белый",
            },
        )

        self.assertEqual(data["packaging"], "1 шт.")
        self.assertEqual(data["sales_unit"], "шт.")
        self.assertEqual(data["barcode"], "1234567890123")
        self.assertTrue(data["status"])

    def test_product_serializer_returns_characteristics(self):
        product = self.create_product()

        characteristic = Characteristic.objects.create(
            name="Номинальный ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="А",
        )

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_number=16,
            status=True,
        )

        data = ProductSerializer(product).data

        self.assertEqual(
            data["characteristics"],
            [
                {
                    "id": product.characteristics.first().id,
                    "name": "Номинальный ток",
                    "value_type": "number",
                    "value": 16.0,
                    "unit": "А",
                    "status": True,
                }
            ],
        )

    def test_inactive_characteristic_is_still_returned_with_status_false(self):
        product = self.create_product()

        characteristic = Characteristic.objects.create(
            name="Номинальный ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="А",
        )

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_number=16,
            status=False,
        )

        data = ProductSerializer(product).data

        self.assertEqual(len(data["characteristics"]), 1)
        self.assertFalse(data["characteristics"][0]["status"])

    def test_optional_references_can_be_null(self):
        product = self.create_product(
            brand=None,
            series=None,
            model=None,
            execution=None,
            color=None,
            protection_degree=None,
        )

        data = ProductSerializer(product).data

        self.assertIsNone(data["brand"])
        self.assertIsNone(data["series"])
        self.assertIsNone(data["model"])
        self.assertIsNone(data["execution"])
        self.assertIsNone(data["color"])
        self.assertIsNone(data["protection_degree"])
