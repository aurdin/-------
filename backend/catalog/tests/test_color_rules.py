from django.test import TestCase
from catalog.services.color_availability import ColorAvailabilityService

from catalog.models import (
    Color,
    Series,
    SeriesColor,
    Type,
    TypeColor,
    Brand,
)


class ColorRulesTests(TestCase):
    def setUp(self):
        self.type = Type.objects.create(
            name="Розетка",
        )

        self.brand = Brand.objects.create(
            name="Legrand",
        )

        self.series = Series.objects.create(
            name="Valena",
            brand=self.brand,
        )

        self.white = Color.objects.create(
            name="Белый",
        )

        self.gray = Color.objects.create(
            name="Серый",
        )

        self.black = Color.objects.create(
            name="Чёрный",
        )

        self.aluminium = Color.objects.create(
            name="Алюминий",
        )

        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )

        TypeColor.objects.create(
            type=self.type,
            color=self.gray,
        )

        TypeColor.objects.create(
            type=self.type,
            color=self.black,
        )

        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
        )

        SeriesColor.objects.create(
            series=self.series,
            color=self.gray,
        )

        SeriesColor.objects.create(
            series=self.series,
            color=self.aluminium,
        )

    def test_color_allowed_when_present_in_type_and_series(self):
        self.assertTrue(
            self.is_color_allowed(
                self.type,
                self.series,
                self.white,
            )
        )

    def test_color_allowed_when_present_only_in_type_without_series_restriction(self):
        series = Series.objects.create(
            name="Unrestricted Series",
            brand=self.brand,
        )

        self.assertTrue(
            self.is_color_allowed(
                self.type,
                series,
                self.black,
            )
        )

    def test_color_allowed_when_present_only_in_series_without_type_restriction(self):
        unrestricted_type = Type.objects.create(
            name="Вилка",
        )

        self.assertTrue(
            self.is_color_allowed(
                unrestricted_type,
                self.series,
                self.aluminium,
            )
        )

    def test_color_allowed_when_type_and_series_have_no_restrictions(self):
        unrestricted_type = Type.objects.create(
            name="Выключатель",
        )

        unrestricted_series = Series.objects.create(
            name="Unrestricted",
            brand=self.brand,
        )

        self.assertTrue(
            self.is_color_allowed(
                unrestricted_type,
                unrestricted_series,
                self.black,
            )
        )

    def test_color_rejected_when_not_allowed_by_series(self):
        self.assertFalse(
            self.is_color_allowed(
                self.type,
                self.series,
                self.black,
            )
        )

    def test_color_rejected_when_not_allowed_by_type(self):
        self.assertFalse(
            self.is_color_allowed(
                self.type,
                self.series,
                self.aluminium,
            )
        )

    def test_inactive_type_color_does_not_allow_color(self):
        TypeColor.objects.filter(
            type=self.type,
            color=self.black,
        ).update(status=False)

        self.assertFalse(
            self.is_color_allowed(
                self.type,
                None,
                self.black,
            )
        )

    def test_inactive_series_color_does_not_allow_color(self):
        SeriesColor.objects.filter(
            series=self.series,
            color=self.aluminium,
        ).update(status=False)

        self.assertFalse(
            self.is_color_allowed(
                Type.objects.create(name="Новый тип"),
                self.series,
                self.aluminium,
            )
        )

    def test_inactive_color_is_not_allowed(self):
        self.black.status = False
        self.black.save(update_fields=("status",))

        self.assertFalse(
            self.is_color_allowed(
                self.type,
                None,
                self.black,
            )
        )

    @staticmethod
    def is_color_allowed(product_type, series, color):
        return ColorAvailabilityService.is_allowed(
            product_type,
            series,
            color,
        )