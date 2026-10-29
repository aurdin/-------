import csv
import hashlib
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO, StringIO

from django.contrib import admin, messages
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import BaseInlineFormSet
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook

from apps.prices.forms import PriceImportConfirmForm, PriceImportForm
from apps.prices.import_service import WorkbookImportError, analyze_import_file
from apps.prices.models import Prices, Promotion, PromotionTarget, OrderDiscountSchedule, OrderDiscountTier


IMPORT_TOKEN_SALT = "prices.import"
IMPORT_TOKEN_MAX_AGE = 30 * 60


@admin.register(Prices)
class PricesAdmin(admin.ModelAdmin):
    export_fields = (
        "article",
        "amount",
        "status",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    actions = (
        "import_xlsx_action",
        "import_csv_action",
        "export_to_excel",
        "export_to_csv",
    )
    show_full_result_count = False

    list_display = ("article", "amount", "status", "valid_from", "valid_to")
    list_filter = ("status",)
    search_fields = ("article", "article_key")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fields = (
        "article",
        "amount",
        "status",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            readonly.extend(("article", "amount", "valid_from", "valid_to"))
        return tuple(readonly)

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_urls(self):
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_file),
                {"file_format": "xlsx"},
                name="prices_prices_import",
            ),
            path(
                "import/csv/",
                self.admin_site.admin_view(self.import_file),
                {"file_format": "csv"},
                name="prices_prices_import_csv",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        import_routes = {
            "import_xlsx_action": "admin:prices_prices_import",
            "import_csv_action": "admin:prices_prices_import_csv",
        }
        if request.method == "POST" and request.POST.get("action") in import_routes:
            if not self.has_add_permission(request):
                raise PermissionDenied
            return redirect(import_routes[request.POST["action"]])
        return super().changelist_view(request, extra_context=extra_context)

    def import_file(self, request, file_format):
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = PriceImportForm(file_format=file_format)
        confirm_form = PriceImportConfirmForm(file_format=file_format)
        preview = None
        confirming = False

        if request.method == "POST" and request.POST.get("action") == "preview":
            form = PriceImportForm(request.POST, request.FILES, file_format=file_format)
            if form.is_valid():
                content = form.cleaned_data["file"].read()
                valid_from = form.cleaned_data.get("valid_from") or timezone.localdate()
                try:
                    preview = analyze_import_file(content, valid_from, file_format)
                except WorkbookImportError as exc:
                    form.add_error("file", str(exc))
                else:
                    token = signing.dumps(
                        {
                            "sha256": hashlib.sha256(content).hexdigest(),
                            "valid_from": valid_from.isoformat(),
                            "file_format": file_format,
                        },
                        salt=IMPORT_TOKEN_SALT,
                        compress=True,
                    )
                    confirm_form = PriceImportConfirmForm(
                        initial={"confirm_token": token},
                        file_format=file_format,
                    )

        elif request.method == "POST" and request.POST.get("action") == "confirm":
            confirming = True
            confirm_form = PriceImportConfirmForm(
                request.POST,
                request.FILES,
                file_format=file_format,
            )
            if confirm_form.is_valid():
                content = confirm_form.cleaned_data["file"].read()
                try:
                    token_data = signing.loads(
                        confirm_form.cleaned_data["confirm_token"],
                        salt=IMPORT_TOKEN_SALT,
                        max_age=IMPORT_TOKEN_MAX_AGE,
                    )
                except signing.BadSignature:
                    confirm_form.add_error(
                        None,
                        _("The preview expired or is invalid. Preview the file again."),
                    )
                else:
                    file_hash = hashlib.sha256(content).hexdigest()
                    valid_from = parse_date(token_data.get("valid_from", ""))
                    if (
                        file_hash != token_data.get("sha256")
                        or token_data.get("file_format") != file_format
                        or valid_from is None
                    ):
                        confirm_form.add_error(
                            "file",
                            _("Select the same file that was previewed."),
                        )
                    else:
                        try:
                            preview = analyze_import_file(
                                content,
                                valid_from,
                                file_format,
                            )
                        except WorkbookImportError as exc:
                            confirm_form.add_error("file", str(exc))
                        else:
                            if not preview["can_confirm"]:
                                confirm_form.add_error(
                                    None,
                                    _("The file can no longer be imported. Preview it again."),
                                )
                            else:
                                created = 0
                                try:
                                    with transaction.atomic():
                                        for row in preview["valid_rows"]:
                                            Prices.objects.create(
                                                article=row["article"],
                                                amount=Decimal(row["amount"]),
                                                valid_from=valid_from,
                                                created_by=request.user,
                                                updated_by=request.user,
                                            )
                                            created += 1
                                except ValidationError as exc:
                                    confirm_form.add_error(
                                        None,
                                        "; ".join(str(message) for message in exc.messages),
                                    )
                                else:
                                    skipped = preview["total_rows"] - created
                                    messages.success(
                                        request,
                                        _(
                                            "Import complete: %(created)s added; %(skipped)s skipped."
                                        )
                                        % {"created": created, "skipped": skipped},
                                    )
                                    return redirect("admin:prices_prices_changelist")

        title = (
            _("Import base prices from XLSX")
            if file_format == "xlsx"
            else _("Import base prices from CSV")
        )
        import_url = reverse(
            "admin:prices_prices_import"
            if file_format == "xlsx"
            else "admin:prices_prices_import_csv"
        )
        context = {
            **self.admin_site.each_context(request),
            "title": title,
            "opts": self.model._meta,
            "form": form,
            "confirm_form": confirm_form,
            "confirming": confirming,
            "preview": preview,
            "file_format": file_format,
            "changelist_url": reverse("admin:prices_prices_changelist"),
            "import_url": import_url,
        }
        return render(request, "admin/prices/prices/import_form.html", context)

    @admin.action(description=_("Import from Excel"), permissions=["add"])
    def import_xlsx_action(self, request, queryset):
        return redirect("admin:prices_prices_import")

    @admin.action(description=_("Import from CSV"), permissions=["add"])
    def import_csv_action(self, request, queryset):
        return redirect("admin:prices_prices_import_csv")

    def _iter_export_rows(self, queryset):
        queryset = queryset.select_related("created_by", "updated_by")
        for price in queryset:
            yield (
                price.article,
                price.amount,
                price.status,
                price.valid_from,
                price.valid_to,
                timezone.localtime(price.created_at).replace(tzinfo=None),
                timezone.localtime(price.updated_at).replace(tzinfo=None),
                price.created_by.get_username() if price.created_by else None,
                price.updated_by.get_username() if price.updated_by else None,
            )

    @admin.action(description=_("Export XLSX"))
    def export_to_excel(self, request, queryset):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Prices"
        worksheet.append(list(self.export_fields))

        for row in self._iter_export_rows(queryset):
            worksheet.append(row)
            article_cell = worksheet.cell(row=worksheet.max_row, column=1)
            article_cell.data_type = "s"
            article_cell.number_format = "@"

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for column in worksheet.columns:
            column_letter = column[0].column_letter
            worksheet.column_dimensions[column_letter].width = min(
                max(max(len(str(cell.value or "")) for cell in column) + 2, 14),
                32,
            )

        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        filename = f"base-prices-{timezone.localdate().isoformat()}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @admin.action(description=_("Export CSV"))
    def export_to_csv(self, request, queryset):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(self.export_fields)

        for row in self._iter_export_rows(queryset):
            writer.writerow(
                value.isoformat() if isinstance(value, (date, datetime))
                else str(value) if isinstance(value, Decimal)
                else value
                for value in row
            )

        response = HttpResponse(
            "\ufeff" + output.getvalue(),
            content_type="text/csv; charset=utf-8",
        )
        filename = f"base-prices-{timezone.localdate().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class PromotionTargetInline(admin.TabularInline):
    model = PromotionTarget
    extra = 1
    fields = ("article", "category", "group", "type", "color")


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_percent", "allow_other_discounts", "status", "valid_from", "valid_to")
    list_filter = ("status",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fields = (
        "name",
        "description",
        "discount_percent",
        "allow_other_discounts",
        "status",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    inlines = (PromotionTargetInline,)

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class OrderDiscountTierInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        ranges = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            data = form.cleaned_data
            if not data or data.get("DELETE"):
                continue
            minimum = data.get("min_order_amount")
            maximum = data.get("max_order_amount")
            if minimum is not None:
                ranges.append((minimum, maximum))
        for index, (minimum_a, maximum_a) in enumerate(ranges):
            for minimum_b, maximum_b in ranges[index + 1:]:
                overlap = (
                    (maximum_a is None or minimum_b < maximum_a)
                    and (maximum_b is None or minimum_a < maximum_b)
                )
                if overlap:
                    raise ValidationError(
                        _("Order discount tiers in one schedule must not overlap.")
                    )


class OrderDiscountTierInline(admin.TabularInline):
    model = OrderDiscountTier
    formset = OrderDiscountTierInlineFormSet
    extra = 1
    fields = (
        "min_order_amount",
        "max_order_amount",
        "discount_percent",
    )


@admin.register(OrderDiscountSchedule)
class OrderDiscountScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "valid_from", "valid_to")
    list_filter = ("status",)
    search_fields = ("name",)
    ordering = ("-valid_from", "name")
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "status",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
    )
    inlines = (OrderDiscountTierInline,)
