from django.urls import path

from .views import (
    StockAdjustmentView,
    StockDetailView,
    StockListView,
    StockPlaceOrderView,
    StockReceiveView,
    StockReleaseView,
    StockReserveView,
    StockSellView,
    StockShipFromSupplierView,
    StockStatusView,
    WarehouseDetailView,
    WarehouseListView,
)


urlpatterns = [
    path("warehouses/", WarehouseListView.as_view(), name="warehouse-list"),
    path(
        "warehouses/<int:pk>/", WarehouseDetailView.as_view(), name="warehouse-detail"
    ),
    path("stock/", StockListView.as_view(), name="stock-list"),
    path("stock/<int:pk>/", StockDetailView.as_view(), name="stock-detail"),
    path("stock/<int:pk>/reserve/", StockReserveView.as_view(), name="stock-reserve"),
    path("stock/<int:pk>/release/", StockReleaseView.as_view(), name="stock-release"),
    path("stock/<int:pk>/sell/", StockSellView.as_view(), name="stock-sell"),
    path("stock/<int:pk>/receive/", StockReceiveView.as_view(), name="stock-receive"),
    path(
        "stock/<int:pk>/adjustment/",
        StockAdjustmentView.as_view(),
        name="stock-adjustment",
    ),
    path(
        "stock/<int:pk>/place-order/",
        StockPlaceOrderView.as_view(),
        name="stock-place-order",
    ),
    path(
        "stock/<int:pk>/ship-from-supplier/",
        StockShipFromSupplierView.as_view(),
        name="stock-ship-from-supplier",
    ),
    path(
        "stock/<int:pk>/update-status/",
        StockStatusView.as_view(),
        name="stock-update-status",
    ),
]
