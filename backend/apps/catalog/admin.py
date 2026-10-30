"""Admin configuration for product catalog models."""

from zipfile import BadZipFile

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin  # type: ignore
from openpyxl.utils.exceptions import InvalidFileException  # type: ignore

from apps.catalog.models import (
    Product,
    ProductCharacteristic,
    ProductNameRule,
    ProductNameRuleComponent,
)
from apps.catalog.services.product_import import ProductImportService
from apps.directory.services.export_admin import DirectoryExportAdminMixin, DirectoryImportForm
from apps.directory.services.import_service import DirectoryImportService


class ProductCharacteristicInline(admin.TabularInline):
    model = ProductCharacteristic
    extra = 0


class ProductAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    list_display = ("prd_code", "prd_article", "prd_name_ru", "status", "date_created")
    list_filter = ("status", "type")
    search_fields = (
        "prd_code",
        "prd_article",
        "prd_name_en",
        "prd_name_ru",
        "prd_name_uk",
    )
    readonly_fields = ("prd_code", "date_created", "prd_name_en", "prd_name_ru", "prd_name_uk")
    inlines = (ProductCharacteristicInline,)
    fieldsets = (
        (
            None,
            {"fields": ("prd_code", "prd_article", ("prd_name_en", "prd_name_ru", "prd_name_uk"))},
        ),
        (
            _("Product classification"),
            {
                "fields": (
                    "category", "group", "type", "type_model", "execution",
                    "protection_degree", "color", "supply_variant", "brand", "series",
                )
            },
        ),
        (
            _("Details"),
            {
                "fields": (
                    "prd_description", "prd_notes", "status", "date_created",
                    "packaging", "sales_unit", "barcode",
                )
            },
        ),
        (_("Product photos"), {"fields": ("product_image_1", "product_image_2", "product_image_3")}),
    )

    def import_from_excel(self, request):
        form = DirectoryImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            try:
                headers, rows = DirectoryImportService.read_workbook(
                    form.cleaned_data["file"]
                )
                DirectoryImportService.validate_headers(self.model, headers)
                if not rows:
                    raise ValidationError(_("The Excel file contains no data rows."))
                result = ProductImportService.import_rows(rows)
                for error in result["errors"]:
                    messages.error(
                        request,
                        _("Row %(row)s: %(message)s") % error,
                    )
                if result["cancelled"]:
                    messages.error(
                        request,
                        _(
                            "Import cancelled: more than 10 rows contain errors; "
                            "no changes were saved."
                        ),
                    )
                else:
                    messages.success(
                        request,
                        _("Import completed. Created: %(created)s; updated: %(updated)s.")
                        % result,
                    )
                return redirect(
                    reverse(
                        f"admin:{self.model._meta.app_label}_"
                        f"{self.model._meta.model_name}_changelist"
                    )
                )
            except ValidationError as exc:
                form.add_error(
                    "file",
                    "; ".join(str(message) for message in exc.messages),
                )
            except (BadZipFile, InvalidFileException, OSError):
                form.add_error("file", _("The uploaded file is not a valid Excel workbook."))

        context = {
            **self.admin_site.each_context(request),
            "title": _("Import products from Excel"),
            "opts": self.model._meta,
            "form": form,
        }
        return render(request, "admin/common/directory/import_form.html", context)


class ProductNameRuleComponentInline(admin.TabularInline):
    model = ProductNameRuleComponent
    extra = 1
    ordering = ("position",)


@admin.register(Product)
class RegisteredProductAdmin(ProductAdmin):
    pass


@admin.register(ProductNameRule)
class ProductNameRuleAdmin(admin.ModelAdmin):
    list_display = ("type",)
    inlines = (ProductNameRuleComponentInline,)
