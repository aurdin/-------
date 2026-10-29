from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.prices.models import Prices


def normalize_article(article):
    return (article or "").strip().upper()


def select_base_price(article, on_date=None):
    article_key = normalize_article(article)
    if not article_key:
        return None

    on_date = on_date or timezone.localdate()
    return (
        Prices.objects.filter(
            article_key=article_key,
            status=True,
            valid_from__lte=on_date,
        )
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=on_date))
        .order_by("-valid_from", "-created_at", "-pk")
        .first()
    )


def get_base_price_amount(article, on_date=None):
    price = select_base_price(article, on_date)
    return price.amount if price is not None else Decimal("0.00")
