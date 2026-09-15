from django.test import TestCase

from catalog.models import (
    Brand,
    Color,
    Series,
    SeriesColor,
    Type,
    TypeColor,
)
from catalog.services.color_availability import ColorAvailabilityService


class ColorAvailabilityServiceTests(TestCase):
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

    def test_no_type_restrictions_allows_active_color(self):
        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.white,
            )
        )

    def test_no_series_restrictions_does_not_restrict_type_allowed_color(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.white,
            )
        )

    def test_type_restriction_allows_listed_color(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.white,
            )
        )

    def test_type_restriction_rejects_unlisted_color(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.black,
            )
        )

    def test_series_restriction_allows_listed_color(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.white,
            )
        )

    def test_series_restriction_rejects_unlisted_color(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
        )

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.black,
            )
        )

    def test_type_and_series_use_intersection(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )
        TypeColor.objects.create(
            type=self.type,
            color=self.gray,
        )

        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
        )
        SeriesColor.objects.create(
            series=self.series,
            color=self.aluminium,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.white,
            )
        )

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.gray,
            )
        )

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.aluminium,
            )
        )

    def test_inactive_type_color_does_not_create_restriction(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
            status=False,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.white,
            )
        )

    def test_inactive_series_color_does_not_create_restriction(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
            status=False,
        )

        self.assertTrue(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.white,
            )
        )

    def test_inactive_color_is_always_rejected(self):
        self.white.status = False
        self.white.save(update_fields=("status",))

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.white,
            )
        )

    def test_inactive_color_is_rejected_even_if_allowed_by_type(self):
        TypeColor.objects.create(
            type=self.type,
            color=self.white,
        )

        self.white.status = False
        self.white.save(update_fields=("status",))

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                None,
                self.white,
            )
        )

    def test_inactive_color_is_rejected_even_if_allowed_by_series(self):
        SeriesColor.objects.create(
            series=self.series,
            color=self.white,
        )

        self.white.status = False
        self.white.save(update_fields=("status",))

        self.assertFalse(
            ColorAvailabilityService.is_allowed(
                self.type,
                self.series,
                self.white,
            )
        )
