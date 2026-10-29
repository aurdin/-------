from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.prices.models import Prices
from apps.prices.services import normalize_article, select_base_price


def serialize_price(price):
    return {
        "id": price.pk,
        "article": price.article,
        "amount": str(price.amount),
        "currency": "UAH",
        "status": price.status,
        "valid_from": price.valid_from.isoformat(),
        "valid_to": price.valid_to.isoformat() if price.valid_to else None,
        "created_at": price.created_at.isoformat(),
        "updated_at": price.updated_at.isoformat(),
    }


class PriceListView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        article = request.query_params.get("article")
        prices = Prices.objects.all()
        if article is not None:
            article_key = normalize_article(article)
            if not article_key:
                return Response(
                    {"detail": "Параметр article не должен быть пустым."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            prices = prices.filter(article_key=article_key)

        return Response({"results": [serialize_price(item) for item in prices]})


class CurrentPriceView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        article = request.query_params.get("article", "")
        if not normalize_article(article):
            return Response(
                {"detail": "Параметр article обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_date = request.query_params.get("date")
        on_date = parse_date(raw_date) if raw_date else None
        if raw_date and on_date is None:
            return Response(
                {"detail": "Параметр date должен быть датой в формате YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price = select_base_price(article, on_date)
        if price is None:
            return Response(
                {
                    "article": article.strip(),
                    "amount": "0.00",
                    "currency": "UAH",
                    "price_id": None,
                },
                status=status.HTTP_200_OK,
            )

        data = serialize_price(price)
        data["price_id"] = data.pop("id")
        return Response(data, status=status.HTTP_200_OK)


class PriceHistoryView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        article = request.query_params.get("article", "")
        article_key = normalize_article(article)
        if not article_key:
            return Response(
                {"detail": "Параметр article обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prices = Prices.objects.filter(article_key=article_key)
        return Response({"results": [serialize_price(item) for item in prices]})
