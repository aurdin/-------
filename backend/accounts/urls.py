from django.urls import path

from .views import (
    CustomerAddressListView,
    CustomerProfileView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    CustomerAddressDetailView,
)


urlpatterns = [
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="auth-register",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="auth-login",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="auth-logout",
    ),
    path(
        "auth/me/",
        MeView.as_view(),
        name="auth-me",
    ),
    path(
        "customer/profile/",
        CustomerProfileView.as_view(),
        name="customer-profile",
    ),
    path(
        "customer/addresses/",
        CustomerAddressListView.as_view(),
        name="customer-addresses",
    ),
    path(
        "customer/addresses/<int:pk>/",
        CustomerAddressDetailView.as_view(),
        name="customer-address-detail",
    ),
]
