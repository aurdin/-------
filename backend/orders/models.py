from django.conf import settings
from django.db import models
from django.db.models import Q


class OrderStatus(models.TextChoices):
    NEW = "new", "Новый"
    CONFIRMED = "confirmed", "Подтверждён"
    PROCESSING = "processing", "В обработке"
    COMPLETED = "completed", "Завершён"
    CANCELLED = "cancelled", "Отменён"


class Order(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    currency = models.ForeignKey(
        "prices.Currency",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    number = models.CharField(
        max_length=30,
        unique=True,
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )

    customer_name = models.CharField(
        max_length=450,
    )
    customer_phone = models.CharField(
        max_length=30,
    )

    delivery_first_name = models.CharField(
        max_length=150,
    )
    delivery_last_name = models.CharField(
        max_length=150,
    )
    delivery_middle_name = models.CharField(
        max_length=150,
        blank=True,
    )
    delivery_phone = models.CharField(
        max_length=30,
    )
    delivery_country = models.CharField(
        max_length=100,
    )
    delivery_region = models.CharField(
        max_length=150,
        blank=True,
    )
    delivery_city = models.CharField(
        max_length=150,
    )
    delivery_postal_code = models.CharField(
        max_length=20,
        blank=True,
    )
    delivery_address_line = models.CharField(
        max_length=255,
    )
    delivery_apartment = models.CharField(
        max_length=50,
        blank=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    product_discount_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    order_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    promotion_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="ck_order_subtotal_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(product_discount_total__gte=0),
                name="ck_order_product_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(order_discount__gte=0),
                name="ck_order_order_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(promotion_discount__gte=0),
                name="ck_order_promotion_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    Q(order_discount__gte=0)
                    & Q(promotion_discount__gte=0)
                    & Q(
                        order_discount__lte=(
                            models.F("subtotal") - models.F("promotion_discount")
                        )
                    )
                ),
                name="ck_order_final_discount_lte_subtotal",
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="ck_order_total_nonnegative",
            ),
        )

    def __str__(self):
        return f"Order {self.number}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    article = models.CharField(
        max_length=100,
    )
    product_name = models.CharField(
        max_length=255,
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="ck_order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gt=0),
                name="ck_order_item_unit_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(discount__gte=0),
                name="ck_order_item_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="ck_order_item_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount__lte=models.F("unit_price")),
                name="ck_order_item_discount_lte_unit_price",
            ),
            models.UniqueConstraint(
                fields=("order", "product"),
                name="uq_order_item_order_product",
            ),
        )

    def __str__(self):
        return f"Order {self.order.number} — {self.product_name} × {self.quantity}"
