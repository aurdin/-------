"""Admin configuration for product catalog models."""

from zipfile import BadZipFile

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin  # type: ignore
from openpyxl.utils.exceptions import InvalidFileException  # type: ignore
from django.forms.models import BaseInlineFormSet
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from apps.directory.characteristics.models import CharacteristicValue, Unit

from apps.catalog.models import (
    Product,
    ProductCharacteristic,
    ProductNameRule,
    ProductNameRuleComponent,
)
from apps.catalog.forms import ProductCharacteristicAdminForm
from apps.catalog.services.product_import import ProductImportService
from apps.directory.services.export_admin import DirectoryExportAdminMixin, DirectoryImportForm
from apps.directory.services.import_service import DirectoryImportService


class ProductCharacteristicInline(admin.TabularInline):
    model = ProductCharacteristic
    form = ProductCharacteristicAdminForm
    extra = 0
    classes = ("product-characteristics",)
    fields = ("characteristic", "value", "unit", "status")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        value_field = formset.form.base_fields["value"]
        if not isinstance(value_field.widget, RelatedFieldWidgetWrapper):
            related_admin = self.admin_site._registry.get(CharacteristicValue)
            value_field.widget = RelatedFieldWidgetWrapper(
                value_field.widget,
                ProductCharacteristic._meta.get_field("value_reference").remote_field,
                self.admin_site,
                can_add_related=bool(related_admin and related_admin.has_add_permission(request)),
                can_change_related=bool(related_admin and related_admin.has_change_permission(request)),
                can_delete_related=bool(related_admin and related_admin.has_delete_permission(request)),
                can_view_related=bool(related_admin and related_admin.has_view_permission(request)),
            )
        unit_field = formset.form.base_fields["unit"]
        if not isinstance(unit_field.widget, RelatedFieldWidgetWrapper):
            unit_admin = self.admin_site._registry.get(Unit)
            unit_field.widget = RelatedFieldWidgetWrapper(
                unit_field.widget,
                ProductCharacteristic._meta.get_field("unit").remote_field,
                self.admin_site,
                can_add_related=bool(unit_admin and unit_admin.has_add_permission(request)),
                can_change_related=bool(unit_admin and unit_admin.has_change_permission(request)),
                can_delete_related=bool(unit_admin and unit_admin.has_delete_permission(request)),
                can_view_related=bool(unit_admin and unit_admin.has_view_permission(request)),
            )
        return formset

class ProductAdmin(DirectoryExportAdminMixin, TranslationAdmin):
    actions = ("copy_selected_products",)
    list_display = ("prd_code", "prd_article", "prd_name_ru", "status", "date_created")

    @admin.action(description=_("Copy selected products"))
    def copy_selected_products(self, request, queryset):
        copied = 0
        with transaction.atomic():
            for product in queryset.prefetch_related("characteristics"):
                base_article = f"COPY-{product.prd_article}"
                article = base_article
                suffix = 2
                while Product.objects.filter(prd_article=article).exists():
                    article = f"{base_article}-{suffix}"
                    suffix += 1

                values = {}
                for field in Product._meta.concrete_fields:
                    if field.primary_key or field.name in {"prd_code", "prd_article", "date_created"}:
                        continue
                    values[field.attname] = getattr(product, field.attname)

                duplicate = Product(**values, prd_article=article)
                duplicate.save()

                for characteristic in product.characteristics.all():
                    characteristic_values = {
                        field.attname: getattr(characteristic, field.attname)
                        for field in ProductCharacteristic._meta.concrete_fields
                        if not field.primary_key and field.name != "product"
                    }
                    ProductCharacteristic.objects.create(
                        product=duplicate,
                        **characteristic_values,
                    )
                copied += 1

        self.message_user(
            request,
            _("Created %(count)s product copies.") % {"count": copied},
            messages.SUCCESS,
        )
    list_display = ("prd_code", "prd_article", "prd_name_ru", "status", "date_created")
    list_filter = ("status", "type")
    search_fields = (
        "prd_code",
        "prd_article",
        "prd_name_en",
        "prd_name_ru",
        "prd_name_uk",
    )
    readonly_fields = (
        "prd_code",
        "date_created",
        "prd_name_en",
        "prd_name_ru",
        "prd_name_uk",
        "prd_description_en",
        "prd_description_ru",
        "prd_description_uk",
        "prd_characteristics_en",
        "prd_characteristics_ru",
        "prd_characteristics_uk",
    )
    inlines = (ProductCharacteristicInline,)
    fieldsets = (
        (
            None,
            {"fields": ("prd_code", "prd_article", ("prd_name_en", "prd_name_ru", "prd_name_uk"))},
        ),
        (
            _("Product classification"),
            {
                "classes": ("product-classification",),
                "fields": (
                    "category", "group", "type", "type_model", "execution",
                    "protection_degree", "color", "supply_variant", "brand", "series",
                )
            },
        ),
        (
            _("Product photos"),
            {
                "classes": ("product-photos",),
                "fields": ("product_image_1", "product_image_2", "product_image_3"),
            },
        ),
        (
            _("Details"),
            {
                "classes": ("product-details",),
                "fields": (
                    "prd_description", "prd_characteristics", "prd_notes",
                    "status", "date_created",
                    "packaging", "sales_unit", "barcode",
                ),
            },
        ),
    )

    class Media:
        js = (
            "admin/catalog/product_form_order.js",
            "admin/catalog/product_characteristic_values_v5.js",
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


class ProductNameRuleComponentInlineFormSet(BaseInlineFormSet):
    def next_position(self):
        max_position = self.get_queryset().aggregate(max_position=Max("position"))[
            "max_position"
        ] or 0
        return max_position + 1

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        initial_count = self.initial_form_count()
        if not self.is_bound and isinstance(i, int) and i >= initial_count:
            form.initial["position"] = self.next_position() + i - initial_count
        return form

    @property
    def empty_form(self):
        form = super().empty_form
        if not self.is_bound:
            form.initial["position"] = self.next_position()
        return form


class ProductNameRuleComponentInline(admin.TabularInline):
    model = ProductNameRuleComponent
    extra = 1
    fields = ("position", "component", "characteristic")
    ordering = ("position",)
    formset = ProductNameRuleComponentInlineFormSet

    class Media:
        js = ("admin/catalog/product_name_rule_v2.js",)


@admin.register(Product)
class RegisteredProductAdmin(ProductAdmin):
    pass


@admin.register(ProductNameRule)
class ProductNameRuleAdmin(admin.ModelAdmin):
    list_display = ("group",)
    inlines = (ProductNameRuleComponentInline,)
