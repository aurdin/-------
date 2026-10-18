from django.contrib import admin
from modeltranslation.admin import TranslationAdmin  # type: ignore

from directory.services.export_admin import DirectoryExportAdminMixin

from .forms import (
    CharacteristicForm,
    CharacteristicGroupForm,
    CharacteristicValueForm,
    UnitForm,
)

from .models import (
    Characteristic,
    CharacteristicGroup,
    CharacteristicValue,
    Unit,
)


@admin.register(CharacteristicGroup)
class CharacteristicGroupAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = CharacteristicGroupForm
    list_display = (
        "chg_code",
        "chg_name",
        "chg_status",
        "date_updated",
    )

    list_filter = ("chg_status",)

    search_fields = (
        "chg_code",
        "chg_name",
        "chg_description",
    )

    readonly_fields = (
        "chg_code",
        "date_created",
        "date_updated",
    )


@admin.register(Unit)
class UnitAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = UnitForm
    list_display = (
        "unt_code",
        "unt_name",
        "unt_symbol",
        "unt_status",
        "date_updated",
    )

    list_filter = ("unt_status",)

    search_fields = (
        "unt_code",
        "unt_name",
        "unt_symbol",
    )

    readonly_fields = (
        "unt_code",
        "date_created",
        "date_updated",
    )


@admin.register(Characteristic)
class CharacteristicAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = CharacteristicForm
    list_display = (
        "chr_code",
        "chr_name",
        "chr_group",
        "chr_unit",
        "chr_status",
        "date_updated",
    )

    list_filter = (
        "chr_group",
        "chr_status",
    )

    search_fields = (
        "chr_code",
        "chr_name",
        "chr_description",
    )

    readonly_fields = (
        "chr_code",
        "date_created",
        "date_updated",
    )

@admin.register(CharacteristicValue)
class CharacteristicValueAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    form = CharacteristicValueForm

    list_display = (
        "cv_code",
        "cv_characteristic",
        "cv_value",
        "cv_status",
        "date_updated",
    )

    list_display_links = ("cv_code",)

    list_filter = (
        "cv_status",
        "cv_characteristic",
    )

    search_fields = (
        "cv_code",
        "cv_value",
        "cv_characteristic__chr_name",
        "cv_characteristic__chr_code",
    )

    ordering = (
        "cv_characteristic__chr_name",
        "cv_value",
    )

    readonly_fields = (
        "cv_code",
        "date_created",
        "date_updated",
    )

    list_per_page = 50