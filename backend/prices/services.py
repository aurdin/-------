from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q

from prices.models import Discount, Price

def get_current_price(product, at, currency=None):
    prices = Price.objects.filter(
        product=product,
        valid_from__lte=at,
    ).filter(Q(valid_to__isnull=True) | Q(valid_to__gt=at))

    if currency is not None:
        prices = prices.filter(currency=currency)

    return prices.order_by("-valid_from").first()


def get_current_discount(product, at):
    discounts = Discount.objects.filter(
        product=product,
        is_active=True,
        valid_from__lte=at,
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gt=at)
    ).order_by("-valid_from")

    return discounts.first()


def calculate_final_price(price, discount=None):
    if price is None:
        raise ValidationError("Price is required.")

    amount = price.amount

    if discount is None:
        return amount

    if discount.type == Discount.DISCOUNT_TYPE_PERCENT:
        result = amount * (
        Decimal("1") - discount.value / Decimal("100")  # noqa: FURB157
    )
    elif discount.type == Discount.DISCOUNT_TYPE_FIXED:
        result = amount - discount.value
    else:
        raise ValidationError("Unknown discount type.")

    result = result.quantize(Decimal("0.01"))

    return max(result, Decimal("0.00"))

def validate_discount_period(discount):
    queryset = Discount.objects.filter(
        product=discount.product,
        is_active=True,
    ).exclude(
        pk=discount.pk,
    )

    if discount.valid_to is None:
        overlapping = queryset.filter(
            Q(valid_to__isnull=True)
            | Q(valid_to__gt=discount.valid_from)
        )
    else:
        overlapping = queryset.filter(
            valid_from__lt=discount.valid_to,
        ).filter(
            Q(valid_to__isnull=True)
            | Q(valid_to__gt=discount.valid_from)
        )

    if overlapping.exists():
        raise ValidationError(
            "Discount period overlaps with another active discount."
        )

def create_discount(
    *,
    product,
    discount_type,
    value,
    valid_from,
    valid_to=None,
    is_active=True,
):
    discount = Discount(
        product=product,
        type=discount_type,
        value=value,
        valid_from=valid_from,
        valid_to=valid_to,
        is_active=is_active,
    )

    discount.full_clean()

    if discount.is_active:
        validate_discount_period(discount)

    discount.save()

    return discount

_UNSET = object()

def update_discount(
    discount,
    *,
    discount_type=_UNSET,
    value=_UNSET,
    valid_from=_UNSET,
    valid_to=_UNSET,
    is_active=_UNSET,
):
    if discount_type is not _UNSET:
        discount.type = discount_type

    if value is not _UNSET:
        discount.value = value

    if valid_from is not _UNSET:
        discount.valid_from = valid_from

    if valid_to is not _UNSET:
        discount.valid_to = valid_to

    if is_active is not _UNSET:
        discount.is_active = is_active

    discount.full_clean()

    if discount.is_active:
        validate_discount_period(discount)

    discount.save()

    return discount

def get_calculated_price(product, at, currency):
    price = get_current_price(
        product,
        at,
        currency=currency,
    )

    if price is None:
        return None

    discount = get_current_discount(
        product,
        at,
    )

    final_price = calculate_final_price(
        price,
        discount,
    )

    return {
        "price": price,
        "discount": discount,
        "final_price": final_price,
    }