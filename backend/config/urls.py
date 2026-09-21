from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("stock.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("prices.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("orders.urls")),
]
