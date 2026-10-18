from django import forms
from django.utils.translation import gettext_lazy as _


class UniqueTranslatedNameForm(forms.ModelForm):
    """Проверка уникальности названий на всех поддерживаемых языках."""

    name_fields = ()
    duplicate_message = _("An entry with this name already exists.")

    def clean(self):
        cleaned_data = super().clean()

        for field_name in self.name_fields:
            value = cleaned_data.get(field_name)

            if not value or not value.strip():
                continue

            duplicates = self._meta.model.objects.filter(
                **{f"{field_name}__iexact": value.strip()}
            )

            if self.instance and self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)

            if duplicates.exists():
                self.add_error(field_name, self.duplicate_message)

        return cleaned_data
