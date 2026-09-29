from modeltranslation.translator import TranslationOptions, register

from apps.catalog.models import Category


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )
