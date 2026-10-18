from django.utils.translation import gettext_lazy as _

from directory.forms import UniqueTranslatedNameForm

from .models import (
    Brand,
    Category,
    Color,
    Execution,
    Group,
    Series,
    SupplyVariant,
    Type,
    TypeModel,
)


class CategoryForm(UniqueTranslatedNameForm):
    name_fields = ("cat_name_en", "cat_name_ru", "cat_name_uk")
    duplicate_message = _("A category with this name already exists.")

    class Meta:
        model = Category
        fields = "__all__"


class GroupForm(UniqueTranslatedNameForm):
    name_fields = ("grp_name_en", "grp_name_ru", "grp_name_uk")
    duplicate_message = _("A group with this name already exists.")

    class Meta:
        model = Group
        fields = "__all__"


class BrandForm(UniqueTranslatedNameForm):
    name_fields = ("brd_name_en", "brd_name_ru", "brd_name_uk")
    duplicate_message = _("A brand with this name already exists.")

    class Meta:
        model = Brand
        fields = "__all__"


class SeriesForm(UniqueTranslatedNameForm):
    name_fields = ("ser_name_en", "ser_name_ru", "ser_name_uk")
    duplicate_message = _("A series with this name already exists.")

    class Meta:
        model = Series
        fields = "__all__"


class TypeForm(UniqueTranslatedNameForm):
    name_fields = ("typ_name_en", "typ_name_ru", "typ_name_uk")
    duplicate_message = _("A type with this name already exists.")

    class Meta:
        model = Type
        fields = "__all__"


class ColorForm(UniqueTranslatedNameForm):
    name_fields = ("clr_name_en", "clr_name_ru", "clr_name_uk")
    duplicate_message = _("A color with this name already exists.")

    class Meta:
        model = Color
        fields = "__all__"


class TypeModelForm(UniqueTranslatedNameForm):
    name_fields = ("mdl_name_en", "mdl_name_ru", "mdl_name_uk")
    duplicate_message = _("A type model with this name already exists.")

    class Meta:
        model = TypeModel
        fields = "__all__"


class ExecutionForm(UniqueTranslatedNameForm):
    name_fields = ("exc_name_en", "exc_name_ru", "exc_name_uk")
    duplicate_message = _("An execution with this name already exists.")

    class Meta:
        model = Execution
        fields = "__all__"


class SupplyVariantForm(UniqueTranslatedNameForm):
    name_fields = ("sup_name_en", "sup_name_ru", "sup_name_uk")
    duplicate_message = _("A supply variant with this name already exists.")

    class Meta:
        model = SupplyVariant
        fields = "__all__"
