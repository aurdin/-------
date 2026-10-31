from django.utils.translation import gettext_lazy as _
from apps.directory.forms import UniqueTranslatedNameForm
from .models import Characteristic, CharacteristicGroup, Unit, CharacteristicValue
from django import forms

class CharacteristicGroupForm(UniqueTranslatedNameForm):
    name_fields = ("chg_name_en", "chg_name_ru", "chg_name_uk")
    duplicate_message = _("A characteristic group with this name already exists.")

    class Meta:
        model = CharacteristicGroup
        fields = "__all__"


class UnitForm(UniqueTranslatedNameForm):
    name_fields = ("unt_name_en", "unt_name_ru", "unt_name_uk")
    duplicate_message = _("A unit with this name already exists.")

    class Meta:
        model = Unit
        fields = "__all__"


class CharacteristicForm(UniqueTranslatedNameForm):
    name_fields = ("chr_name_en", "chr_name_ru", "chr_name_uk")
    duplicate_message = _("A characteristic with this name already exists.")

    class Meta:
        model = Characteristic
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            return cleaned_data

        new_value_type = cleaned_data.get("chr_value_type")
        old_value_type = Characteristic.objects.filter(pk=self.instance.pk).values_list(
            "chr_value_type", flat=True
        ).first()
        if new_value_type != old_value_type:
            from apps.catalog.models import ProductCharacteristic

            if ProductCharacteristic.objects.filter(
                characteristic_id=self.instance.pk
            ).exists():
                self.add_error(
                    "chr_value_type",
                    _("The value type cannot be changed while products use this characteristic."),
                )
        return cleaned_data

class CharacteristicValueForm(forms.ModelForm):
    name_fields = ("cv_value_en", "cv_value_ru", "cv_value_uk")
    duplicate_message = _("A characteristic value with this name already exists.")

    class Meta:
        model = CharacteristicValue
        fields = "__all__"
