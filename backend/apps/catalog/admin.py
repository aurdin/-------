from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.catalog.models import Category


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = (
        "name",
        "status",
        "date_created",
        "date_updated",
    )

    list_filter = ("status",)
    search_fields = ("name", "description")
    ordering = ("name",)
