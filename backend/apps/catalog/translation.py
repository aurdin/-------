"""Переводы товарных полей каталога."""
from modeltranslation.translator import TranslationOptions, register  # type: ignore

from .models import Product


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("prd_name", "prd_description", "prd_characteristics", "prd_notes")
