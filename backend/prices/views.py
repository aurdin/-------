from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from catalog.models import Product
from prices.models import Price, Currency, Discount
from prices.serializers import CurrencySerializer, PriceSerializer, DiscountSerializer
from django.utils import timezone
from prices.services import (
    get_calculated_price,
    get_current_price
)

class PriceListView(APIView):
    def get(self, request):
        prices = Price.objects.select_related(
            "currency",
            "product",
        ).order_by("-valid_from", "-id")

        serializer = PriceSerializer(prices, many=True)

        return Response(
            {
                "results": serializer.data,
                "message": (
                    "Цены не найдены." if not serializer.data else "Цены получены."
                ),
            },
            status=status.HTTP_200_OK,
        )


class PriceDetailView(APIView):
    def get(self, request, pk):
        try:
            price = Price.objects.select_related(
                "currency",
                "product",
            ).get(pk=pk)
        except Price.DoesNotExist:
            return Response(
                {"detail": "Цена не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PriceSerializer(price)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    
class CurrentPriceView(APIView):
    def get(self, request, product_id):
        currency_code = request.query_params.get("currency")

        if not currency_code:
            return Response(
                {"detail": "Параметр currency обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            currency = Currency.objects.get(
                code=currency_code,
                is_active=True,
            )
        except Currency.DoesNotExist:
            return Response(
                {"detail": "Валюта не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Товар не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        price = get_current_price(
            product,
            timezone.now(),
            currency=currency,
        )

        if price is None:
            return Response(
                {"detail": "Текущая цена не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PriceSerializer(price)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class CurrencyListView(APIView):
    def get(self, request):
        currencies = Currency.objects.all().order_by(
            "-is_active",
            "code",
        )

        serializer = CurrencySerializer(
            currencies,
            many=True,
        )

        return Response(
            {
                "results": serializer.data,
                "message": (
                    "Валюты не найдены." if not serializer.data else "Валюты получены."
                ),
            },
            status=status.HTTP_200_OK,
        )


class CurrencyDetailView(APIView):
    def get(self, request, pk):
        try:
            currency = Currency.objects.get(pk=pk)
        except Currency.DoesNotExist:
            return Response(
                {"detail": "Валюта не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CurrencySerializer(currency)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    
class DiscountListView(APIView):
    def get(self, request):
        discounts = Discount.objects.select_related(
            "product",
        ).order_by("-valid_from", "-id")

        serializer = DiscountSerializer(
            discounts,
            many=True,
        )

        return Response(
            {
                "results": serializer.data,
                "message": (
                    "Скидки не найдены." if not serializer.data else "Скидки получены."
                ),
            },
            status=status.HTTP_200_OK,
        )


class DiscountDetailView(APIView):
    def get(self, request, pk):
        try:
            discount = Discount.objects.select_related(
                "product",
            ).get(pk=pk)
        except Discount.DoesNotExist:
            return Response(
                {"detail": "Скидка не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DiscountSerializer(discount)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class CalculatedPriceView(APIView):
    def get(self, request, product_id):
        currency_code = request.query_params.get("currency")

        if not currency_code:
            return Response(
                {"detail": "Параметр currency обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            currency = Currency.objects.get(
                code=currency_code,
                is_active=True,
            )
        except Currency.DoesNotExist:
            return Response(
                {"detail": "Валюта не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Товар не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        calculated = get_calculated_price(
            product,
            timezone.now(),
            currency,
        )

        if calculated is None:
            return Response(
                {"detail": "Текущая цена не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        discount = calculated["discount"]

        return Response(
            {
                "product": product.id,
                "currency": currency.code,
                "price": str(calculated["price"].amount),
                "discount": (str(discount.value) if discount is not None else None),
                "discount_type": (discount.type if discount is not None else None),
                "final_price": str(calculated["final_price"]),
            },
            status=status.HTTP_200_OK,
        )  
    
class ProductPriceHistoryView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Товар не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        prices = (
            Price.objects.select_related(
                "currency",
            )
            .filter(
                product=product,
            )
            .order_by(
                "-valid_from",
                "-id",
            )
        )

        discounts = Discount.objects.filter(
            product=product,
        ).order_by(
            "-valid_from",
            "-id",
        )

        price_serializer = PriceSerializer(
            prices,
            many=True,
        )

        discount_serializer = DiscountSerializer(
            discounts,
            many=True,
        )

        return Response(
            {
                "product": product.id,
                "prices": price_serializer.data,
                "discounts": discount_serializer.data,
            },
            status=status.HTTP_200_OK,
        )    