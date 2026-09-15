from django.urls import path

from cart.views import CartItemDetailView, CartItemView, CartView


urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemView.as_view(), name="cart-items"),
    path(
        "cart/items/<int:pk>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
]
