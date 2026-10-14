from zipfile import BadZipFile

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from openpyxl.utils.exceptions import InvalidFileException # type: ignore

from .export import DirectoryExportService
from .import_service import DirectoryImportService


class DirectoryImportForm(forms.Form):
    """Форма загрузки Excel-файла для импорта справочника."""

    file = forms.FileField(
        label=_("Excel file"),
    )


class DirectoryExportAdminMixin:
    """Добавляет универсальные импорт и экспорт справочника в Excel."""

    change_list_template = "admin/common/directory/change_list.html"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "export/",
                self.admin_site.admin_view(self.export_to_excel),
                name=self._get_export_url_name(),
            ),
            path(
                "import/",
                self.admin_site.admin_view(self.import_from_excel),
                name=self._get_import_url_name(),
            ),
        ]

        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        extra_context["export_url_name"] = (
            f"admin:{self._get_export_url_name()}"
        )

        extra_context["import_url_name"] = (
            f"admin:{self._get_import_url_name()}"
        )

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )

    def export_to_excel(self, request):
        output = DirectoryExportService.export(
            self.model.objects.all()
        )

        filename = f"{self.model._meta.model_name}s.xlsx"

        response = HttpResponse(
            output.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        return response

    def import_from_excel(self, request):
        form = DirectoryImportForm(request.POST or None, request.FILES or None)

        if request.method == "POST" and form.is_valid():
            try:
                headers, data = DirectoryImportService.read_workbook(
                    form.cleaned_data["file"]
                )

                DirectoryImportService.validate_headers(
                    self.model,
                    headers,
                )

                if not data:
                    raise ValidationError(
                        _("The Excel file contains no data rows.")
                    )

                prepared_rows = DirectoryImportService.prepare_rows(
                    self.model,
                    data,
                )

                results = DirectoryImportService.import_rows(
                    self.model,
                    prepared_rows,
                )

                created = sum(
                    result["action"] == "create"
                    for result in results
                )

                updated = sum(
                    result["action"] == "update"
                    for result in results
                )

                messages.success(
                    request,
                    _(
                        "Import completed. Created: %(created)s; "
                        "updated: %(updated)s."
                    )
                    % {
                        "created": created,
                        "updated": updated,
                    },
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
                form.add_error(
                    "file",
                    _("The uploaded file is not a valid Excel workbook."),
                )

        context = {
            **self.admin_site.each_context(request),
            "title": _("Import %(model)s from Excel")
            % {"model": self.model._meta.verbose_name},
            "opts": self.model._meta,
            "form": form,
        }

        return render(
            request,
            "admin/common/directory/import_form.html",
            context,
        )

    def _get_export_url_name(self):
        return (
            f"{self.model._meta.app_label}_"
            f"{self.model._meta.model_name}_export"
        )

    def _get_import_url_name(self):
        return (
            f"{self.model._meta.app_label}_"
            f"{self.model._meta.model_name}_import"
        )