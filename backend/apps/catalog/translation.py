from modeltranslation.translator import TranslationOptions, register # type: ignore

from apps.catalog.models import Category


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = (
        "cat_name",
        "cat_description",
    )
