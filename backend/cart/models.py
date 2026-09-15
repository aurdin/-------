from django.conf import settings
from django.db import models
from django.db.models import Q


class Cart(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        unique=True,
    )
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = ( 
            models.CheckConstraint(
                condition=(
                    Q(customer__isnull=False, session_key__isnull=True)
                    | Q(customer__isnull=True, session_key__isnull=False)
                ),
                name="ck_cart_owner",
            ),
        )

    def __str__(self):
        if self.customer_id:
            return f"Cart #{self.pk} — customer {self.customer_id}"
        return f"Cart #{self.pk} — session {self.session_key}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="uq_cart_item_cart_product",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="ck_cart_item_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"Cart #{self.cart_id} — Product #{self.product_id} × {self.quantity}"
