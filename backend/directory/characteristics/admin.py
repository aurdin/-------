from django.contrib import admin

from .models import CharacteristicGroup, Unit


@admin.register(CharacteristicGroup)
class CharacteristicGroupAdmin(admin.ModelAdmin):
    list_display = (
        "chg_code",
        "chg_name",
        "chg_status",
        "date_updated",
    )

    list_filter = ("chg_status",)

    search_fields = (
        "chg_code",
        "chg_name",
    )

    readonly_fields = (
        "chg_code",
        "date_created",
        "date_updated",
    )
    exclude = ("chg_name",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "unt_code",
        "unt_name",
        "unt_symbol",
        "unt_status",
        "date_updated",
    )

    list_filter = ("unt_status",)

    search_fields = (
        "unt_code",
        "unt_name",
        "unt_symbol",
    )

    readonly_fields = (
        "unt_code",
        "date_created",
        "date_updated",
    )
    exclude = ("unt_name",)
