from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.services import get_current_cart
from orders.models import Order
from orders.serializers import (
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)
from orders.services import change_order_status, create_order_from_cart
from prices.models import Currency


class CheckoutView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        currency_code = request.data.get("currency")

        if not currency_code:
            return Response(
                {"currency": ["This field is required."]},
                status=400,
            )

        try:
            currency = Currency.objects.get(
                code=currency_code,
                is_active=True,
            )
        except Currency.DoesNotExist:
            return Response(
                {"currency": ["Invalid currency."]},
                status=400,
            )

        cart = get_current_cart(request)

        try:
            order = create_order_from_cart(
                cart=cart,
                customer=request.user if request.user.is_authenticated else None,
                currency=currency,
                order_data=serializer.validated_data,
                at=timezone.now(),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )

        return Response(
            OrderSerializer(order).data,
            status=201,
        )


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Order.objects.filter(customer=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at", "-id")
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).prefetch_related(
            "items"
        )
class OrderStatusView(APIView):
    permission_classes = (IsAdminUser,)

    def patch(self, request, pk):
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.prefetch_related("items").get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=404,
            )

        try:
            change_order_status(
                order,
                serializer.validated_data["status"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )

        return Response(
            OrderSerializer(order).data,
            status=200,
        )