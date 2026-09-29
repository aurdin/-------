from django.contrib import admin

from apps.catalog.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "date_created",
        "date_updated",
    )

    list_filter = ("status",)

    search_fields = (
        "name",
        "description",
    )

    ordering = ("name",)
