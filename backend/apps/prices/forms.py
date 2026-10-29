from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PriceImportForm(forms.Form):
    file = forms.FileField()
    valid_from = forms.DateField(
        required=False,
        initial=timezone.localdate,
        label=_("Valid from"),
    )

    def __init__(self, *args, file_format="xlsx", **kwargs):
        super().__init__(*args, **kwargs)
        self.file_format = file_format
        self.fields["file"].label = _("Excel file") if file_format == "xlsx" else _("CSV file")
        self.fields["file"].widget.attrs["accept"] = f".{file_format}"

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if not uploaded_file.name.lower().endswith(f".{self.file_format}"):
            message = (
                _("Upload an XLSX workbook.")
                if self.file_format == "xlsx"
                else _("Upload a CSV file.")
            )
            raise ValidationError(message)
        return uploaded_file


class PriceImportConfirmForm(forms.Form):
    file = forms.FileField()
    confirm_token = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, file_format="xlsx", **kwargs):
        super().__init__(*args, **kwargs)
        self.file_format = file_format
        self.fields["file"].label = _("Excel file") if file_format == "xlsx" else _("CSV file")
        self.fields["file"].widget.attrs["accept"] = f".{file_format}"

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if not uploaded_file.name.lower().endswith(f".{self.file_format}"):
            message = (
                _("Upload an XLSX workbook.")
                if self.file_format == "xlsx"
                else _("Upload a CSV file.")
            )
            raise ValidationError(message)
        return uploaded_file
