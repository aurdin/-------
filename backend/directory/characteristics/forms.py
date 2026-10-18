from django.utils.translation import gettext_lazy as _
from directory.forms import UniqueTranslatedNameForm
from .models import Characteristic, CharacteristicGroup, Unit

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
