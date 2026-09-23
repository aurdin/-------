from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Product

def validate_price_amount(amount):
    if amount is None:
        raise ValidationError(
            {"amount": "Price amount is required."}
        )

    if amount <= 0:
        raise ValidationError(
            {"amount": "Price amount must be greater than zero."}
        )

    if amount.as_tuple().exponent < -2:
        raise ValidationError(
            {
                "amount": (
                    "Price amount must have no more than "
                    "2 decimal places."
                )
            }
        )


class Currency(models.Model):
    code = models.CharField(
        max_length=3,
        unique=True,
    )
    name = models.CharField(
        max_length=100,
    )
    symbol = models.CharField(
        max_length=10,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "prices_currency"

    def __str__(self):
        return f"{self.code} — {self.name}"
    
class Price(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="prices",
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="prices",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "prices_price"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="ck_price_amount_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(valid_to__isnull=True)
                    | models.Q(valid_to__gt=models.F("valid_from"))
                ),
                name="ck_price_valid_period",
            ),
        )

    def __str__(self):
        return f"{self.product} — {self.amount} {self.currency.code}"    
    
class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="exchange_rates_base",
    )
    quote_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="exchange_rates_quote",
    )
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=8,
    )
    valid_from = models.DateTimeField()

    class Meta:
        db_table = "prices_exchange_rate"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(rate__gt=0),
                name="ck_exchange_rate_positive",
            ),
            models.CheckConstraint(
                condition=~models.Q(base_currency=models.F("quote_currency")),
                name="ck_exchange_rate_different_currencies",
            ),
            models.UniqueConstraint(
                fields=(
                    "base_currency",
                    "quote_currency",
                    "valid_from",
                ),
                name="uq_exchange_rate_period",
            ),
        )

    def __str__(self):
        return f"{self.base_currency.code} → {self.quote_currency.code}: {self.rate}"
    
class Discount(models.Model):
    DISCOUNT_TYPE_PERCENT = "percent"
    DISCOUNT_TYPE_FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = (
        (DISCOUNT_TYPE_PERCENT, "Percent"),
        (DISCOUNT_TYPE_FIXED, "Fixed"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="discounts",
    )
    type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
    )
    valid_to = models.DateTimeField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "prices_discount"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(value__gt=0),
                name="ck_discount_value_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    type__in=(
                        "percent",
                        "fixed",
                    )
                ),
                name="ck_discount_type_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(valid_to__isnull=True)
                    | models.Q(valid_from__isnull=True)
                    | models.Q(valid_to__gt=models.F("valid_from"))
                ),
                name="ck_discount_valid_period_discount",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        type="percent",
                        value__lte=100,
                    )
                    | models.Q(type="fixed")
                ),
                name="ck_discount_percent_max",
            ),
        )

    def __str__(self):
        return f"{self.product} — {self.value} ({self.type})"

class OrderDiscount(models.Model):
    DISCOUNT_TYPE_PERCENT = "percent"
    DISCOUNT_TYPE_FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = (
        (DISCOUNT_TYPE_PERCENT, "Percent"),
        (DISCOUNT_TYPE_FIXED, "Fixed"),
    )

    name = models.CharField(
        max_length=255,
    )
    type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    max_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
    )
    valid_to = models.DateTimeField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "prices_order_discount"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(value__gt=0),
                name="ck_order_discount_value_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    type__in=(
                        "percent",
                        "fixed",
                    )
                ),
                name="ck_order_discount_type_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        type="percent",
                        value__lte=100,
                    )
                    | models.Q(type="fixed")
                ),
                name="ck_order_discount_percent_max",
            ),
            models.CheckConstraint(
                condition=models.Q(min_order_amount__gte=0),
                name="ck_order_discount_min_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(max_order_amount__isnull=True)
                    | models.Q(max_order_amount__gt=models.F("min_order_amount"))
                ),
                name="ck_order_discount_amount_range",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(valid_to__isnull=True)
                    | models.Q(valid_from__isnull=True)
                    | models.Q(valid_to__gt=models.F("valid_from"))
                ),
                name="ck_order_discount_valid_period",
            ),
        )

    def __str__(self):
        return f"{self.name} — {self.value} ({self.type})"          