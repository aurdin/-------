"""Административный интерфейс для справочников связей SmEl."""
from django.contrib import admin
from directory.services.export_admin import DirectoryExportAdminMixin

from .models import (
    GroupType,
    SeriesType,
    SeriesProductColor,
    SeriesFrameColor,
    TypeModelType,
    TypeExecution,
    TypeCharacteristic,
)


@admin.register(GroupType)
class GroupTypeAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("group", "type", "status")
    list_filter = ("group", "type", "status")
    search_fields = (
        "group__grp_name",
        "type__typ_name",
    )
    ordering = ("group", "type")


@admin.register(SeriesType)
class SeriesTypeAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("series", "type", "status")
    list_filter = ("series", "type", "status")
    search_fields = (
        "series__ser_name",
        "type__typ_name",
    )
    ordering = ("series", "type")


@admin.register(SeriesProductColor)
class SeriesProductColorAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("series", "color", "status")
    list_filter = ("series", "color", "status")
    search_fields = (
        "series__ser_name",
        "color__clr_name",
    )
    ordering = (
        "series__ser_name",
        "color__clr_name",
    )


@admin.register(SeriesFrameColor)
class SeriesFrameColorAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("series", "color", "status")
    list_filter = ("series", "color", "status")
    search_fields = (
        "series__ser_name",
        "color__clr_name",
    )
    ordering = (
        "series__ser_name",
        "color__clr_name",
    )


@admin.register(TypeModelType)
class TypeModelTypeAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("type_model", "type", "status")
    list_filter = ("type_model", "type", "status")
    search_fields = (
        "type_model__mdl_name",
        "type__typ_name",
    )
    ordering = (
        "type_model__mdl_name",
        "type__typ_name",
    )


@admin.register(TypeExecution)
class TypeExecutionAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("type", "execution", "status")
    list_filter = ("type", "execution", "status")
    search_fields = (
        "type__typ_name",
        "execution__exc_name",
    )
    ordering = (
        "type__typ_name",
        "execution__exc_name",
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