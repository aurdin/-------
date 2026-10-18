from django.contrib import admin
from modeltranslation.admin import TranslationAdmin  # type: ignore
from directory.services.export_admin import DirectoryExportAdminMixin
from .forms import (
    CharacteristicForm,
    CharacteristicGroupForm,
    UnitForm,
)

from .models import (
    Characteristic,
    CharacteristicGroup,
    TypeCharacteristic,
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


@admin.register(TypeCharacteristic)
class TypeCharacteristicAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = (
        "tch_type",
        "tch_characteristic",
        "tch_status",
        "date_updated",
    )

    list_filter = (
        "tch_type",
        "tch_characteristic",
        "tch_status",
    )

    search_fields = (
        "tch_type__typ_name",
        "tch_characteristic__chr_name",
    )

    readonly_fields = (
        "date_created",
        "date_updated",
    )