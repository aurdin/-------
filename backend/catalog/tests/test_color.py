from django.db import IntegrityError
from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Color,
    Group,
    Product,
    Series,
    SeriesColor,
    Type,
    TypeColor,
)


class ColorModelTests(TestCase):
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

        self.series = Series.objects.create(
            name="Valena",
            brand=self.brand,
        )

        self.type = Type.objects.create(
            name="Розетка",
        )

        self.color = Color.objects.create(
            name="Белый",
        )

    def test_color_can_be_created(self):
        self.assertEqual(self.color.name, "Белый")
        self.assertTrue(self.color.status)

    def test_color_name_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            Color.objects.create(
                name="Белый",
            )

    def test_type_color_can_be_created(self):
        type_color = TypeColor.objects.create(
            type=self.type,
            color=self.color,
        )

        self.assertEqual(type_color.type, self.type)
        self.assertEqual(type_color.color, self.color)
        self.assertTrue(type_color.status)

    def test_type_color_duplicate_is_rejected(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.color,
        )

        with self.assertRaises(IntegrityError):
            TypeColor.objects.create(
                type=self.type,
                color=self.color,
            )

    def test_series_color_can_be_created(self):
        series_color = SeriesColor.objects.create(
            series=self.series,
            color=self.color,
        )

        self.assertEqual(series_color.series, self.series)
        self.assertEqual(series_color.color, self.color)
        self.assertTrue(series_color.status)

    def test_series_color_duplicate_is_rejected(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.color,
        )

        with self.assertRaises(IntegrityError):
            SeriesColor.objects.create(
                series=self.series,
                color=self.color,
            )

    def test_product_can_reference_color(self):
        product = Product.objects.create(
            article="TEST-COLOR-001",
            category=self.category,
            group=self.group,
            brand=self.brand,
            series=self.series,
            type=self.type,
            color=self.color,
            sales_unit="шт.",
        )

        self.assertEqual(product.color, self.color)

    def test_product_can_exist_without_color(self):
        product = Product.objects.create(
            article="TEST-COLOR-002",
            category=self.category,
            group=self.group,
            brand=self.brand,
            series=self.series,
            type=self.type,
            sales_unit="шт.",
        )

        self.assertIsNone(product.color)

    def test_color_cannot_be_deleted_if_used_by_product(self):
        Product.objects.create(
            article="TEST-COLOR-003",
            category=self.category,
            group=self.group,
            brand=self.brand,
            series=self.series,
            type=self.type,
            color=self.color,
            sales_unit="шт.",
        )

        with self.assertRaises(IntegrityError):
            self.color.delete()

    def test_color_cannot_be_deleted_if_used_by_type_color(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.color,
        )

        with self.assertRaises(IntegrityError):
            self.color.delete()

    def test_color_cannot_be_deleted_if_used_by_series_color(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.color,
        )

        with self.assertRaises(IntegrityError):
            self.color.delete()
