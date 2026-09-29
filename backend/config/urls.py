from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("apps.stock.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.prices.urls")),
    path("api/", include("apps.cart.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.orders.urls")),
]
