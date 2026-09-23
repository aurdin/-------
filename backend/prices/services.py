from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q

from prices.models import Discount, Price, OrderDiscount, ExchangeRate, Currency

def get_current_price(product, at, currency=None):
    prices = Price.objects.filter(
        product=product,
        valid_from__lte=at,
    ).filter(Q(valid_to__isnull=True) | Q(valid_to__gt=at))

    if currency is not None:
        prices = prices.filter(currency=currency)

    return prices.order_by("-valid_from").first()


def get_current_exchange_rate(base_currency, quote_currency, at):
    return (
        ExchangeRate.objects.filter(
            base_currency=base_currency,
            quote_currency=quote_currency,
            valid_from__lte=at,
        )
        .order_by("-valid_from")
        .first()
    )

def convert_amount(amount, rate):
    if amount < Decimal("0.00"):
        raise ValueError("Amount cannot be negative.")

    if rate <= Decimal("0.00"):
        raise ValueError("Rate must be greater than zero.")

    result = amount / rate
    return result.quantize(Decimal("0.01"))

def get_calculated_price_in_currency(product, currency, at):
    uah_price = get_current_price(
        product=product,
        at=at,
        currency=Currency.objects.get(code="UAH"),
    )

    if uah_price is None:
        return None

    discount = get_current_discount(
        product=product,
        at=at,
    )

    final_uah_price = calculate_final_price(
        price=uah_price,
        discount=discount,
    )

    if currency.code == "UAH":
        return {
            "price": uah_price,
            "discount": discount,
            "final_price": final_uah_price,
            "exchange_rate": None,
        }

    exchange_rate = get_current_exchange_rate(
        base_currency=uah_price.currency,
        quote_currency=currency,
        at=at,
    )

    if exchange_rate is None:
        return None

    final_price = convert_amount(
        amount=final_uah_price,
        rate=exchange_rate.rate,
    )

    return {
        "price": uah_price,
        "discount": discount,
        "final_price": final_price,
        "exchange_rate": exchange_rate,
    }

def get_current_discount(product, at):
    discounts = (
        Discount.objects.filter(
            product=product,
            is_active=True,
        )
        .filter(
            Q(valid_from__isnull=True) | Q(valid_from__lte=at),
        )
        .filter(
            Q(valid_to__isnull=True) | Q(valid_to__gt=at),
        )
        .order_by(
            "-valid_from",
        )
    )

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
        starts_before_end = Q()
    else:
        starts_before_end = Q(valid_from__isnull=True) | Q(
            valid_from__lt=discount.valid_to
        )

    if discount.valid_from is None:
        ends_after_start = Q()
    else:
        ends_after_start = Q(valid_to__isnull=True) | Q(
            valid_to__gt=discount.valid_from
        )

    overlapping = queryset.filter(
        starts_before_end,
        ends_after_start,
    )

    if overlapping.exists():
        raise ValidationError("Discount period overlaps with another active discount.")

def create_discount(
    *,
    product,
    discount_type,
    value,
    valid_from=None,
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
def get_current_order_discount(subtotal, at):
    discounts = (
        OrderDiscount.objects.filter(
            is_active=True,
            min_order_amount__lte=subtotal,
        )
        .filter(Q(max_order_amount__isnull=True) | Q(max_order_amount__gt=subtotal))
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=at))
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gt=at))
        .order_by("-min_order_amount", "-valid_from")
    )

    discounts = list(discounts[:2])

    if len(discounts) > 1:
        raise ValidationError("Multiple active order discounts match the subtotal.")

    return discounts[0] if discounts else None

def calculate_order_discount(subtotal, discount=None):
    if subtotal < Decimal("0.00"):
        raise ValidationError("Subtotal cannot be negative.")

    if discount is None:
        return Decimal("0.00")

    if discount.type == OrderDiscount.DISCOUNT_TYPE_PERCENT:
        result = subtotal * discount.value / Decimal(100)

    elif discount.type == OrderDiscount.DISCOUNT_TYPE_FIXED:
        result = discount.value

    else:
        raise ValidationError("Unknown order discount type.")

    result = result.quantize(Decimal("0.01"))

    return min(result, subtotal)

def validate_order_discount_period(discount):
    queryset = OrderDiscount.objects.filter(
        is_active=True,
    ).exclude(
        pk=discount.pk,
    )

    # Пересечение диапазонов сумм:
    # [min_order_amount, max_order_amount)
    amount_overlap = Q(max_order_amount__isnull=True) | Q(
        max_order_amount__gt=discount.min_order_amount
    )

    if discount.max_order_amount is None:
        amount_overlap &= Q()
    else:
        amount_overlap &= Q(min_order_amount__lt=discount.max_order_amount)

    # Пересечение периодов действия:
    # [valid_from, valid_to)
    if discount.valid_to is None:
        starts_before_end = Q()
    else:
        starts_before_end = Q(valid_from__isnull=True) | Q(
            valid_from__lt=discount.valid_to
        )

    if discount.valid_from is None:
        ends_after_start = Q()
    else:
        ends_after_start = Q(valid_to__isnull=True) | Q(
            valid_to__gt=discount.valid_from
        )

    overlapping = queryset.filter(
        amount_overlap,
        starts_before_end,
        ends_after_start,
    )

    if overlapping.exists():
        raise ValidationError(
            "Order discount range and period overlap "
            "with another active order discount."
        )


def create_order_discount(
    *,
    name,
    discount_type,
    value,
    min_order_amount,
    max_order_amount=None,
    valid_from=None,
    valid_to=None,
    is_active=True,
):
    discount = OrderDiscount(
        name=name,
        type=discount_type,
        value=value,
        min_order_amount=min_order_amount,
        max_order_amount=max_order_amount,
        valid_from=valid_from,
        valid_to=valid_to,
        is_active=is_active,
    )

    discount.full_clean()

    if discount.is_active:
        validate_order_discount_period(discount)

    discount.save()

    return discount

def update_order_discount(
    discount,
    *,
    name=_UNSET,
    discount_type=_UNSET,
    value=_UNSET,
    min_order_amount=_UNSET,
    max_order_amount=_UNSET,
    valid_from=_UNSET,
    valid_to=_UNSET,
    is_active=_UNSET,
):
    if name is not _UNSET:
        discount.name = name

    if discount_type is not _UNSET:
        discount.type = discount_type

    if value is not _UNSET:
        discount.value = value

    if min_order_amount is not _UNSET:
        discount.min_order_amount = min_order_amount

    if max_order_amount is not _UNSET:
        discount.max_order_amount = max_order_amount

    if valid_from is not _UNSET:
        discount.valid_from = valid_from

    if valid_to is not _UNSET:
        discount.valid_to = valid_to

    if is_active is not _UNSET:
        discount.is_active = is_active

    discount.full_clean()

    if discount.is_active:
        validate_order_discount_period(discount)

    discount.save()

    return discount