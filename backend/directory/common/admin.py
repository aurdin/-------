from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Category


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = (
        "cat_code",
        "cat_name",
        "cat_status",
        "date_created",
        "date_updated",
    )

    list_filter = ("cat_status",)
    search_fields = ("cat_code", "cat_name", "cat_description")
    ordering = ("cat_name",)