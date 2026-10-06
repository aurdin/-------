from django.contrib import admin
from modeltranslation.admin import TranslationAdmin  # type: ignore

from .models import (
    Brand,
    Category,
    Group,
    GroupType,
    Series,
    Type,
    SeriesType,
    ProtectionDegree,
    Color,
    SeriesProductColor,
    SeriesFrameColor,
    TypeModel,
    TypeModelType,
    Execution,
    TypeExecution,
) 


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = (
        "cat_code",
        "cat_name",
        "cat_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("cat_status",)
    search_fields = ("cat_code", "cat_name", "cat_description")
    ordering = ("cat_name",)


@admin.register(Group)
class GroupAdmin(TranslationAdmin):
    list_display = (
        "grp_code",
        "grp_name",
        "grp_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("grp_status",)
    search_fields = ("grp_code", "grp_name", "grp_description")
    ordering = ("grp_name",)


@admin.register(Brand)
class BrandAdmin(TranslationAdmin):
    list_display = (
        "brd_code",
        "brd_name",
        "brd_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("brd_status",)
    search_fields = ("brd_code", "brd_name", "brd_description")
    ordering = ("brd_name",)


@admin.register(Series)
class SeriesAdmin(TranslationAdmin):
    list_display = (
        "ser_code",
        "brand",
        "ser_name",
        "ser_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("ser_status", "brand")
    search_fields = (
        "ser_code",
        "ser_name",
        "ser_description",
        "brand__brd_name",
    )
    ordering = ("ser_name",)


@admin.register(Type)
class TypeAdmin(TranslationAdmin):
    list_display = (
        "typ_code",
        "typ_name",
        "typ_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("typ_status",)
    search_fields = ("typ_code", "typ_name", "typ_description")
    ordering = ("typ_name",)


@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "type",
    )

    list_filter = ("group", "type")
    search_fields = (
        "group__grp_name",
        "type__typ_name",
    )
    ordering = ("group", "type")

@admin.register(SeriesType)
class SeriesTypeAdmin(admin.ModelAdmin):
    list_display = (
        "series",
        "type",
    )
    list_filter = ("series", "type")
    search_fields = (
        "series__ser_name",
        "type__typ_name",
    )
    ordering = ("series", "type")

@admin.register(ProtectionDegree)
class ProtectionDegreeAdmin(TranslationAdmin):
    list_display = (
        "ptd_code",
        "ptd_name",
        "ptd_status",
        "date_created",
        "date_updated",
    )
    list_filter = ("ptd_status",)
    search_fields = (
        "ptd_code",
        "ptd_name",
        "ptd_description",
    )
    ordering = ("ptd_name",)  


@admin.register(Color)
class ColorAdmin(TranslationAdmin):
    list_display = (
        "clr_code",
        "clr_name",
        "clr_status",
        "date_created",
        "date_updated",
    )
    list_filter = ("clr_status",)
    search_fields = (
        "clr_code",
        "clr_name",
        "clr_description",
    )
    ordering = ("clr_name",)      


@admin.register(SeriesProductColor)
class SeriesProductColorAdmin(admin.ModelAdmin):
    list_display = (
        "series",
        "color",
    )
    list_filter = (
        "series",
        "color",
    )
    search_fields = (
        "series__ser_name",
        "color__clr_name",
    )
    ordering = (
        "series__ser_name",
        "color__clr_name",
    ) 

    
@admin.register(SeriesFrameColor)
class SeriesFrameColorAdmin(admin.ModelAdmin):
    list_display = (
        "series",
        "color",
    )
    list_filter = (
        "series",
        "color",
    )
    search_fields = (
        "series__ser_name",
        "color__clr_name",
    )
    ordering = (
        "series__ser_name",
        "color__clr_name",
    )       


@admin.register(TypeModel)
class TypeModelAdmin(TranslationAdmin):
    list_display = (
        "mdl_code",
        "mdl_name",
        "mdl_status",
        "date_created",
        "date_updated",
    )
    list_filter = ("mdl_status",)
    search_fields = (
        "mdl_code",
        "mdl_name",
        "mdl_description",
    )
    ordering = ("mdl_name",)


@admin.register(TypeModelType)
class TypeModelTypeAdmin(admin.ModelAdmin):
    list_display = (
        "type_model",
        "type",
    )
    list_filter = (
        "type_model",
        "type",
    )
    search_fields = (
        "type_model__mdl_name",
        "type__typ_name",
    )
    ordering = (
        "type_model__mdl_name",
        "type__typ_name",
    ) 


@admin.register(Execution)
class ExecutionAdmin(TranslationAdmin):
    list_display = (
        "exc_code",
        "exc_name",
        "exc_status",
        "date_created",
        "date_updated",
    )
    list_filter = ("exc_status",)
    search_fields = (
        "exc_code",
        "exc_name",
        "exc_description",
    )
    ordering = ("exc_name",) 



@admin.register(TypeExecution)
class TypeExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "execution",
    )
    list_filter = (
        "type",
        "execution",
    )
    search_fields = (
        "type__typ_name",
        "execution__exc_name",
    )
    ordering = (
        "type__typ_name",
        "execution__exc_name",
    )              