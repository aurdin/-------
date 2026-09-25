from decimal import Decimal

from django.db import transaction

from orders.models import Order, OrderItem, OrderStatus, OrderNumberSequence
from prices.services import get_calculated_price_in_currency
from catalog.services.product_name import ProductNameService
from django.utils import timezone


@transaction.atomic
def create_order_from_cart(
    *,
    cart,
    customer,
    currency,
    order_data,
    at,
):
    cart_items = list(
        cart.items.select_related("product").all()
    )

    if not cart_items:
        raise ValueError("Cart is empty.")

    subtotal = Decimal("0.00")
    product_discount_total = Decimal("0.00")

    calculated_items = []

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
        discount = calculated["discount"]

        item_total = (
            unit_price * cart_item.quantity
        ).quantize(Decimal("0.01"))

        subtotal += item_total

        calculated_items.append(
            {
                "cart_item": cart_item,
                "unit_price": unit_price,
                "discount": discount,
                "total": item_total,
            }
        )

    order = Order.objects.create(
        customer=customer,
        currency=currency,
        exchange_rate=None,
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
        order_discount=Decimal("0.00"),
        promotion_discount=Decimal("0.00"),
        total=subtotal,
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
            discount=Decimal("0.00"),
            total=calculated["total"],
        )

        cart.items.all().delete()

        if cart.customer_id is None and cart.session_key is not None:
            cart.session_key = None
            cart.status = "free"
            cart.save(update_fields=("session_key", "status", "updated_at"))

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

    if new_status not in allowed_transitions.get(order.status, set()):
        raise ValueError(
            f"Invalid order status transition: {order.status} -> {new_status}"
        )

    order.status = new_status
    order.save(update_fields=("status", "updated_at"))

    return order

def generate_order_number():
    today = timezone.now().strftime("%Y%m%d")

    sequence, _  = (
        OrderNumberSequence.objects
        .select_for_update()
        .get_or_create(
            pk=1,
            defaults={"value": 0},
        )
    )

    sequence.value += 1
    sequence.save(update_fields=("value",))

    return f"SMEL-{today}-{sequence.value:06d}"   