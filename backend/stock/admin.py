from django.contrib import admin

from .models import Stock, StockPolicy, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = (
        "code",
        "name",
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "warehouse",
        "quantity_available",
        "quantity_reserved",
        "quantity_incoming",
        "quantity_on_order",
        "status",
        "is_discontinued",
        "updated_at",
    )
    list_filter = (
        "warehouse",
        "status",
        "is_discontinued",
    )
    search_fields = (
        "product__article",
        "warehouse__code",
        "warehouse__name",
    )
    readonly_fields = ("updated_at",)


@admin.register(StockPolicy)
class StockPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "low_stock_threshold",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
