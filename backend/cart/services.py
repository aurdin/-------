from django.contrib.auth import get_user_model
from django.db import transaction

from cart.models import Cart, CartItem, CartStatus


User = get_user_model()


@transaction.atomic
def promote_guest_cart_to_customer(cart, customer):
    if cart.customer_id is not None:
        raise ValueError("Cart already belongs to a customer.")

    if cart.session_key is None:
        raise ValueError("Cart is not a guest cart.")

    if Cart.objects.filter(customer=customer).exists():
        raise ValueError("Customer already has a personal cart.")

    cart.customer = customer
    cart.session_key = None
    cart.status = CartStatus.BUSY

    cart.save(
        update_fields=[
            "customer",
            "session_key",
            "status",
            "updated_at",
        ]
    )

    return cart


@transaction.atomic
def merge_guest_cart_with_customer_cart(guest_cart, customer):
    if guest_cart.customer_id is not None:
        raise ValueError("Cart already belongs to a customer.")

    if guest_cart.session_key is None:
        raise ValueError("Cart is not a guest cart.")

    try:
        personal_cart = Cart.objects.get(customer=customer)
    except Cart.DoesNotExist:
        raise ValueError("Customer does not have a personal cart.")

    for guest_item in guest_cart.items.all():
        personal_item, created = CartItem.objects.get_or_create(
            cart=personal_cart,
            product=guest_item.product,
            defaults={"quantity": guest_item.quantity},
        )

        if not created:
            personal_item.quantity += guest_item.quantity
            personal_item.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ]
            )

    guest_cart.items.all().delete()

    guest_cart.customer = None
    guest_cart.session_key = None
    guest_cart.status = CartStatus.FREE

    guest_cart.save(
        update_fields=[
            "customer",
            "session_key",
            "status",
            "updated_at",
        ]
    )

    return personal_cart


@transaction.atomic
def attach_guest_cart_to_customer(session_key, customer):
    if not session_key:
        return Cart.objects.get_or_create(
            customer=customer,
            defaults={"status": CartStatus.BUSY},
        )[0]

    try:
        guest_cart = Cart.objects.get(
            session_key=session_key,
            customer__isnull=True,
            status=CartStatus.BUSY,
        )
    except Cart.DoesNotExist:
        return Cart.objects.get_or_create(
            customer=customer,
            defaults={"status": CartStatus.BUSY},
        )[0]

    if Cart.objects.filter(customer=customer).exists():
        return merge_guest_cart_with_customer_cart(
            guest_cart,
            customer,
        )

    return promote_guest_cart_to_customer(
        guest_cart,
        customer,
    )
