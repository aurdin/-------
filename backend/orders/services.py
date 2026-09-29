from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from catalog.services.product_name import ProductNameService
from orders.models import Order, OrderItem, OrderStatus, OrderNumberSequence
from prices.services import (
    calculate_final_price,
    convert_amount,
    get_calculated_price_in_currency,
    get_current_exchange_rate,
)
from prices.models import Currency


@transaction.atomic
def create_order_from_cart(
    *,
    cart,
    customer,
    currency,
    order_data,
    at,
):
    cart_items = list(cart.items.select_related("product").all())

    if not cart_items:
        raise ValueError("Cart is empty.")

    subtotal = Decimal("0.00")
    product_discount_total = Decimal("0.00")

    calculated_items = []

    exchange_rate = None

    if currency.code != "UAH":
        exchange_rate = get_current_exchange_rate(
            base_currency=Currency.objects.get(code="UAH"),
            quote_currency=currency,
            at=at,
        )

        if exchange_rate is None:
            raise ValueError(f"No current exchange rate for currency {currency.code}.")

    for cart_item in cart_items:
        calculated = get_calculated_price_in_currency(
            product=cart_item.product,
            currency=currency,
            at=at,
        )

        if calculated is None:
            raise ValueError(
                f"No current price for product {cart_item.product.article}."
            )

        unit_price = calculated["final_price"]

        discount_amount_uah = (
            calculated["price"].amount
            - calculate_final_price(
                price=calculated["price"],
                discount=calculated["discount"],
            )
        ).quantize(Decimal("0.01"))

        if currency.code == "UAH":
            discount_amount = discount_amount_uah
        else:
            discount_amount = convert_amount(
                amount=discount_amount_uah,
                rate=calculated["exchange_rate"].rate,
            ).quantize(Decimal("0.01"))

        item_total = (
            unit_price * cart_item.quantity
        ).quantize(Decimal("0.01"))

        subtotal += item_total

        product_discount_total += (
            discount_amount * cart_item.quantity
        ).quantize(Decimal("0.01"))

        calculated_items.append(
            {
                "cart_item": cart_item,
                "unit_price": unit_price,
                "discount": discount_amount,
                "total": item_total,
            }
        )        

        

    order_discount = order_data.get(
        "order_discount",
        Decimal("0.00"),
    )

    promotion_discount = order_data.get(
        "promotion_discount",
        Decimal("0.00"),
    )

    remaining_amount = subtotal

    if order_discount + promotion_discount > remaining_amount:
        raise ValueError("Order discounts exceed the remaining order amount.")

    total = (subtotal - order_discount - promotion_discount).quantize(Decimal("0.01"))

    order = Order.objects.create(
        customer=customer,
        currency=currency,
        exchange_rate=(exchange_rate.rate if exchange_rate is not None else None),
        number=generate_order_number(),
        status=OrderStatus.NEW,
        customer_name=order_data["customer_name"],
        customer_phone=order_data["customer_phone"],
        delivery_first_name=order_data["delivery_first_name"],
        delivery_last_name=order_data["delivery_last_name"],
        delivery_middle_name=order_data.get(
            "delivery_middle_name",
            "",
        ),
        delivery_phone=order_data.get(
            "delivery_phone",
            order_data["customer_phone"],
        ),
        delivery_country=order_data["delivery_country"],
        delivery_region=order_data.get(
            "delivery_region",
            "",
        ),
        delivery_city=order_data["delivery_city"],
        delivery_postal_code=order_data.get(
            "delivery_postal_code",
            "",
        ),
        delivery_address_line=order_data["delivery_address_line"],
        delivery_apartment=order_data.get(
            "delivery_apartment",
            "",
        ),
        subtotal=subtotal,
        product_discount_total=product_discount_total,
        order_discount=order_discount,
        promotion_discount=promotion_discount,
        total=total,
    )

    for calculated in calculated_items:
        cart_item = calculated["cart_item"]

        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            article=cart_item.product.article,
            product_name=ProductNameService.build(cart_item.product),
            quantity=cart_item.quantity,
            unit_price=calculated["unit_price"],
            discount=calculated["discount"],
            total=calculated["total"],
        )

    cart.items.all().delete()

    if cart.customer_id is None and cart.session_key is not None:
        cart.session_key = None
        cart.status = "free"
        cart.save(
            update_fields=(
                "session_key",
                "status",
                "updated_at",
            )
        )

    return order


def change_order_status(order, new_status):
    allowed_transitions = {
        OrderStatus.NEW: {
            OrderStatus.CONFIRMED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.CONFIRMED: {
            OrderStatus.PROCESSING,
            OrderStatus.CANCELLED,
        },
        OrderStatus.PROCESSING: {
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.COMPLETED: set(),
        OrderStatus.CANCELLED: set(),
    }

    if new_status not in allowed_transitions.get(
        order.status,
        set(),
    ):
        raise ValueError(
            f"Invalid order status transition: {order.status} -> {new_status}"
        )

    order.status = new_status
    order.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    return order


def generate_order_number():
    today = timezone.now().strftime("%Y%m%d")

    sequence, _ = OrderNumberSequence.objects.select_for_update().get_or_create(
        pk=1,
        defaults={"value": 0},
    )

    sequence.value += 1
    sequence.save(update_fields=("value",))

    return f"SMEL-{today}-{sequence.value:06d}"
