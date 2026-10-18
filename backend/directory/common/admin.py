from django.contrib import admin
from django.http import HttpResponse  # noqa: F401
from django.urls import path  # noqa: F401
from modeltranslation.admin import TranslationAdmin  # type: ignore
from django.utils.translation import gettext_lazy as _  # noqa: F401
from directory.services.export import DirectoryExportService  # noqa: F401
from directory.services.export_admin import DirectoryExportAdminMixin
from .forms import (
    BrandForm,
    CategoryForm,
    ColorForm,
    ExecutionForm,
    GroupForm,
    SeriesForm,
    SupplyVariantForm,
    TypeForm,
    TypeModelForm,
)
from .models import (
    Brand,
    Category,
    Group,
    Series,
    Type,
    ProtectionDegree,
    Color,
    TypeModel,
    Execution,
    SupplyVariant,
) 

# 1. Справочник категорий
@admin.register(Category)
class CategoryAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = CategoryForm
    list_display = (
        "cat_code",
        "cat_name",
        "cat_status",
        "cat_description",
    )

    list_filter = ("cat_status",)
    search_fields = ("cat_code", "cat_name", "cat_description")
    ordering = ("cat_name",)


# 2. Справочник групп
@admin.register(Group)
class GroupAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = GroupForm
    list_display = (
        "grp_code",
        "grp_name",
        "grp_status",
        "grp_description",
    )

    list_filter = ("grp_status",)
    search_fields = ("grp_code", "grp_name", "grp_description")
    ordering = ("grp_name",)

# 3. Справочник брендов
@admin.register(Brand)
class BrandAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = BrandForm
    list_display = (
        "brd_code",
        "brd_name",
        "brd_status",
        "brd_description",
    )

    list_filter = ("brd_status",)

    search_fields = (
        "brd_code",
        "brd_name",
        "brd_description",
    )

    ordering = ("brd_name",)


 # 4. Справочник серий
@admin.register(Series)
class SeriesAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = SeriesForm
    list_display = (
        "ser_code",
        "brand",
        "ser_name",
        "ser_status",
        "ser_description",
    )

    list_filter = ("ser_status", "brand")
    search_fields = (
        "ser_code",
        "ser_name",
        "ser_description",
        "brand__brd_name",
    )
    ordering = ("ser_name",)


# 5. Справочник типов
@admin.register(Type)
class TypeAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = TypeForm
    list_display = (
        "typ_code",
        "typ_name",
        "typ_status",
        "typ_description",
    )

    list_filter = ("typ_status",)
    search_fields = ("typ_code", "typ_name", "typ_description")
    ordering = ("typ_name",)


# 6. Справочник степеней защиты
@admin.register(ProtectionDegree)
class ProtectionDegreeAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    list_display = (
        "ptd_code",
        "ptd_name",
        "ptd_status",
        "ptd_description",
    )
    list_filter = ("ptd_status",)
    search_fields = (
        "ptd_code",
        "ptd_name",
        "ptd_description",
    )
    ordering = ("ptd_name",)  


 # 7. Справочник цветов
@admin.register(Color)
class ColorAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = ColorForm
    list_display = (
        "clr_code",
        "clr_name",
        "clr_status",
        "clr_description",
    )
    list_filter = ("clr_status",)
    search_fields = (
        "clr_code",
        "clr_name",
        "clr_description",
    )
    ordering = ("clr_name",)      

# 8. Справочник моделей типов
@admin.register(TypeModel)
class TypeModelAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = TypeModelForm
    list_display = (
        "mdl_code",
        "mdl_name",
        "mdl_status",
        "mdl_description",
    )
    list_filter = ("mdl_status",)
    search_fields = (
        "mdl_code",
        "mdl_name",
        "mdl_description",
    )
    ordering = ("mdl_name",)


# 9. Справочник исполнений
@admin.register(Execution)
class ExecutionAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = ExecutionForm
    list_display = (
        "exc_code",
        "exc_name",
        "exc_status",
        "exc_description",
    )
    list_filter = ("exc_status",)
    search_fields = (
        "exc_code",
        "exc_name",
        "exc_description",
    )
    ordering = ("exc_name",) 


# 10. Справочник вариантов поставки
@admin.register(SupplyVariant)
class SupplyVariantAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    form = SupplyVariantForm
    list_display = (
        "sup_code",
        "sup_name",
        "sup_status",
        "sup_description",
    )

    list_filter = ("sup_status",)
    search_fields = (
        "sup_code",
        "sup_name",
        "sup_description",
    )
    ordering = ("sup_name",)