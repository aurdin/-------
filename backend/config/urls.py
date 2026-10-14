from django.contrib import admin
from django.urls import include, path
import config.admin_site  # noqa: F401


urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]
