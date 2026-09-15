from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from cart.serializers import CartItemSerializer, CartSerializer


def get_current_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            customer=request.user,
            defaults={"status": True},
        )
        return cart

    if not request.session.session_key:
        request.session.create()

    cart, _ = Cart.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={"status": True},
    )
    return cart


class CartView(APIView):
    permission_classes = (AllowAny,)  

    def get(self, request):
        cart = get_current_cart(request)
        return Response(CartSerializer(cart).data)

    def delete(self, request):
        cart = get_current_cart(request)
        cart.items.all().delete()

        return Response(status=204)


class CartItemView(APIView):
    permission_classes = (AllowAny,) 

    def post(self, request):
        cart = get_current_cart(request)

        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": quantity},
            )

            if not created:
                item.quantity += quantity
                item.save(update_fields=["quantity", "updated_at"])

        return Response(
            CartItemSerializer(item).data,
            status=201,
        )
#---------
class CartItemDetailView(APIView):
    permission_classes = (AllowAny,)  

    def patch(self, request, pk):
        cart = get_current_cart(request)

        try:
            item = CartItem.objects.get(
                pk=pk,
                cart=cart,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=404,
            )

        if "product_id" in request.data:
            return Response(
                {"product_id": ["This field cannot be changed."]},
                status=400,
            )

        serializer = CartItemSerializer(
            item,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            CartItemSerializer(item).data,
            status=200,
        )

    def delete(self, request, pk):
        cart = get_current_cart(request)

        try:
            item = CartItem.objects.get(
                pk=pk,
                cart=cart,
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=404,
            )

        item.delete()

        return Response(status=204)