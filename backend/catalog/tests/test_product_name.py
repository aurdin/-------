from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Characteristic,
    CharacteristicValue,
    Color,
    Execution,
    Group,
    Model,
    Product,
    ProductCharacteristic,
    Series,
    Type,
)
from catalog.services.product_name import ProductNameService


class ProductNameServiceTests(TestCase):
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
            "sales_unit": "шт.",
        }

        defaults.update(kwargs)

        product = Product(**defaults)
        product.full_clean()
        product.save()

        return product

    def test_full_name_is_generated_in_required_order(self):
        product = self.create_product(
            protection_degree="IP44",
        )

        name = ProductNameService.build(product)

        self.assertEqual(
            name,
            "Розетка Valena С заземлением IP44 Legrand Life Белый",
        )

    def test_article_is_not_included(self):
        product = self.create_product()

        name = ProductNameService.build(product)

        self.assertNotIn(product.article, name)

    def test_empty_optional_fields_are_skipped(self):
        product = self.create_product(
            brand=None,
            series=None,
            model=None,
            execution=None,
            protection_degree=None,
            color=None,
        )

        name = ProductNameService.build(product)

        self.assertEqual(name, "Розетка")

    def test_color_is_always_last(self):
        product = self.create_product(
            protection_degree="IP20",
        )

        name = ProductNameService.build(product)

        self.assertTrue(name.endswith(" Белый"))

    def test_inactive_color_is_not_included(self):
        self.color.status = False
        self.color.save(update_fields=["status"])

        product = self.create_product()

        name = ProductNameService.build(product)

        self.assertNotIn("Белый", name)

    def test_active_product_characteristic_is_included(self):
        characteristic = Characteristic.objects.create(
            name="Номинальный ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="А",
        )

        ProductCharacteristic.objects.create(
            product=self.create_product(),
            characteristic=characteristic,
            value_number=16,
            status=True,
        )

        product = Product.objects.get(article="TEST-001")

        name = ProductNameService.build(product)

        self.assertIn("16 А", name)

    def test_inactive_product_characteristic_is_not_included(self):
        characteristic = Characteristic.objects.create(
            name="Номинальный ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="А",
        )

        product = self.create_product()

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_number=16,
            status=False,
        )

        name = ProductNameService.build(product)

        self.assertNotIn("16 А", name)

    def test_text_characteristic_is_included(self):
        characteristic = Characteristic.objects.create(
            name="Материал",
            value_type=Characteristic.VALUE_TYPE_TEXT,
        )

        product = self.create_product()

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_text="Термопласт",
            status=True,
        )

        name = ProductNameService.build(product)

        self.assertIn("Термопласт", name)

    def test_boolean_characteristic_is_included(self):
        characteristic = Characteristic.objects.create(
            name="Светодиод",
            value_type=Characteristic.VALUE_TYPE_BOOLEAN,
        )

        product = self.create_product()

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_boolean=True,
            status=True,
        )

        name = ProductNameService.build(product)

        self.assertIn("Да", name)

    def test_reference_characteristic_is_included(self):
        characteristic = Characteristic.objects.create(
            name="Цвет маркировки",
            value_type=Characteristic.VALUE_TYPE_REFERENCE,
        )

        value = CharacteristicValue.objects.create(
            characteristic=characteristic,
            value="Красный",
        )

        product = self.create_product()

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_reference=value,
            status=True,
        )

        name = ProductNameService.build(product)

        self.assertIn("Красный", name)

    def test_characteristic_unit_is_appended(self):
        characteristic = Characteristic.objects.create(
            name="Напряжение",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="В",
        )

        product = self.create_product()

        ProductCharacteristic.objects.create(
            product=product,
            characteristic=characteristic,
            value_number=230,
            status=True,
        )

        name = ProductNameService.build(product)

        self.assertIn("230 В", name)
