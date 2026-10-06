from modeltranslation.translator import TranslationOptions, register  # type: ignore

from .models import CharacteristicGroup, Unit


@register(CharacteristicGroup)
class CharacteristicGroupTranslationOptions(TranslationOptions):
    fields = (
        "chg_name",
        "chg_description",
    )

@register(Unit)
class UnitTranslationOptions(TranslationOptions):

    fields = (
        "unt_name",
    )