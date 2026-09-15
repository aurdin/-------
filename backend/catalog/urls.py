from django.urls import path

from catalog.views import (
    CatalogFiltersView,
    ProductDetailView,
    ProductListView,
)


urlpatterns = [
    path(
        "products/",
        ProductListView.as_view(),
        name="product-list",
    ),
    path(
        "products/<int:pk>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "catalog/filters/",
        CatalogFiltersView.as_view(),
        name="catalog-filters",
    ),
]
