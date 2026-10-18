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
)


@admin.register(GroupType)
class GroupTypeAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("group", "type")
    list_filter = ("group", "type")
    search_fields = (
        "group__grp_name",
        "type__typ_name",
    )
    ordering = ("group", "type")


@admin.register(SeriesType)
class SeriesTypeAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("series", "type")
    list_filter = ("series", "type")
    search_fields = (
        "series__ser_name",
        "type__typ_name",
    )
    ordering = ("series", "type")


@admin.register(SeriesProductColor)
class SeriesProductColorAdmin(DirectoryExportAdminMixin, admin.ModelAdmin):
    list_display = ("series", "color")
    list_filter = ("series", "color")
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
    list_display = ("series", "color")
    list_filter = ("series", "color")
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
    list_display = ("type_model", "type")
    list_filter = ("type_model", "type")
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
    list_display = ("type", "execution")
    list_filter = ("type", "execution")
    search_fields = (
        "type__typ_name",
        "execution__exc_name",
    )
    ordering = (
        "type__typ_name",
        "execution__exc_name",
    )