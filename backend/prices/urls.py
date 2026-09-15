from django.urls import path

from prices.views import (
    CurrencyDetailView,
    CurrencyListView,
    PriceDetailView,
    PriceListView,
    DiscountDetailView,
    DiscountListView,
    CurrentPriceView,
    CalculatedPriceView,
    ProductPriceHistoryView,
)


urlpatterns = [
    path("prices/", PriceListView.as_view(), name="price-list"),
    path(
        "prices/products/<int:product_id>/calculated/",
        CalculatedPriceView.as_view(),
        name="calculated-price",
    ),
    path(
        "prices/<int:pk>/",
        PriceDetailView.as_view(),
        name="price-detail",
    ),
    path(
        "prices/currencies/",
        CurrencyListView.as_view(),
        name="currency-list",
    ),
    path(
        "prices/products/<int:product_id>/current/",
        CurrentPriceView.as_view(),
        name="current-price",
    ),
    path(
        "prices/products/<int:product_id>/",
        ProductPriceHistoryView.as_view(),
        name="product-price-history",
    ),
    path(
        "prices/currencies/<int:pk>/",
        CurrencyDetailView.as_view(),
        name="currency-detail",
    ),
    path(
        "prices/discounts/",
        DiscountListView.as_view(),
        name="discount-list",
    ),
    path(
        "prices/discounts/<int:pk>/",
        DiscountDetailView.as_view(),
        name="discount-detail",
    ),
]
