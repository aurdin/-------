from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import ProductCharacteristic
from apps.directory.characteristics.models import CharacteristicValue, Unit


class CharacteristicValueSelect(forms.Select):
    def __init__(self, characteristic_ids, **kwargs):
        self.characteristic_ids = {
            str(key): str(value) for key, value in characteristic_ids.items()
        }
        super().__init__(**kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        characteristic_id = self.characteristic_ids.get(str(value))
        if characteristic_id:
            option["attrs"]["data-characteristic-id"] = characteristic_id
        return option


class CharacteristicUnitSelect(forms.Select):
    def __init__(self, unit_ids, **kwargs):
        self.unit_ids = {str(key): str(value or "") for key, value in unit_ids.items()}
        super().__init__(**kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        unit_id = self.unit_ids.get(str(value))
        if unit_id:
            option["attrs"]["data-unit-id"] = unit_id
        return option


class CharacteristicValueChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.cv_value


class ProductCharacteristicAdminForm(forms.ModelForm):
    value = CharacteristicValueChoiceField(
        queryset=CharacteristicValue.objects.none(),
        label=_("Value"),
        required=True,
    )
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
        label=_("Unit"),
        required=False,
    )

    class Meta:
        model = ProductCharacteristic
        fields = ("characteristic", "unit", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        values = CharacteristicValue.objects.all().order_by(
            "cv_characteristic_id", "cv_value", "id"
        )
        units = Unit.objects.all().order_by("unt_name")
        self.fields["unit"].queryset = units
        characteristic_field = self.fields["characteristic"]
        unit_ids = dict(
            characteristic_field.queryset.values_list("pk", "chr_unit_id")
        )
        characteristic_wrapper = characteristic_field.widget
        characteristic_widget = getattr(characteristic_wrapper, "widget", characteristic_wrapper)
        characteristic_widget = CharacteristicUnitSelect(
            unit_ids,
            attrs=characteristic_widget.attrs.copy(),
            choices=characteristic_field.choices,
        )
        if isinstance(characteristic_wrapper, RelatedFieldWidgetWrapper):
            characteristic_wrapper.widget = characteristic_widget
        else:
            characteristic_field.widget = characteristic_widget

        self.fields["value"].queryset = values
        value_field = self.fields["value"]
        value_wrapper = value_field.widget
        value_widget = getattr(value_wrapper, "widget", value_wrapper)
        value_widget = CharacteristicValueSelect(
            dict(values.values_list("pk", "cv_characteristic_id")),
            attrs=value_widget.attrs.copy(),
            choices=value_field.choices,
        )
        if isinstance(value_wrapper, RelatedFieldWidgetWrapper):
            value_wrapper.widget = value_widget
        else:
            value_field.widget = value_widget
        self.order_fields(("characteristic", "value", "unit", "status"))

        if self.instance and self.instance.pk and self.instance.characteristic_id:
            self.initial["value"] = self._initial_value_id(values)
            self.initial["unit"] = (
                self.instance.unit_id or self.instance.characteristic.chr_unit_id
            )

    def _initial_value_id(self, values):
        if self.instance.value_reference_id:
            return self.instance.value_reference_id

        value_type = self.instance.characteristic.chr_value_type
        if value_type == "text":
            value = self.instance.value_text
        elif value_type == "number" and self.instance.value_number is not None:
            value = format(Decimal(self.instance.value_number).normalize(), "f")
        elif value_type == "boolean" and self.instance.value_boolean is not None:
            value = "true" if self.instance.value_boolean else "false"
        else:
            return None

        return (
            values.filter(
                cv_characteristic_id=self.instance.characteristic_id,
                cv_value=value,
            )
            .values_list("pk", flat=True)
            .first()
        )

    def clean(self):
        cleaned_data = super().clean()
        characteristic = cleaned_data.get("characteristic")
        selected_value = cleaned_data.get("value")
        if characteristic is None or selected_value is None:
            return cleaned_data

        if selected_value.cv_characteristic_id != characteristic.pk:
            self.add_error(
                "value",
                _("Select a value from the selected characteristic's values."),
            )
            return cleaned_data

        cleaned_data["unit"] = cleaned_data.get("unit") or characteristic.chr_unit

        value_type = characteristic.chr_value_type
        self.instance.value_type = value_type
        self.instance.value_text = None
        self.instance.value_number = None
        self.instance.value_boolean = None
        self.instance.value_reference = None

        if value_type == "text":
            self.instance.value_text = selected_value.cv_value
        elif value_type == "number":
            try:
                self.instance.value_number = Decimal(
                    selected_value.cv_value.replace(",", ".")
                )
            except (InvalidOperation, ValueError):
                self.add_error(
                    "value",
                    _("The selected value must be a number for this characteristic."),
                )
        elif value_type == "boolean":
            normalized = selected_value.cv_value.strip().casefold()
            true_values = {"1", "true", "yes", "да", "так", "on", "вкл", "увімкнено"}
            false_values = {"0", "false", "no", "нет", "ні", "off", "выкл", "вимкнено"}
            if normalized in true_values:
                self.instance.value_boolean = True
            elif normalized in false_values:
                self.instance.value_boolean = False
            else:
                self.add_error(
                    "value",
                    _("The selected value must represent true or false for this characteristic."),
                )
        elif value_type == "reference":
            self.instance.value_reference = selected_value
        else:
            self.add_error("characteristic", _("Unsupported characteristic value type."))

        return cleaned_data
