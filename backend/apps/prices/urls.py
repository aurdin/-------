from django.urls import path

from apps.prices.views import CurrentPriceView, PriceHistoryView, PriceListView


urlpatterns = [
    path("", PriceListView.as_view(), name="price-list"),
    path("current/", CurrentPriceView.as_view(), name="current-price"),
    path("history/", PriceHistoryView.as_view(), name="price-history"),
]
