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

    def clean(self):
        validate_price_amount(self.amount)

    def __str__(self):
        return f"{self.product} — {self.amount} {self.currency.code}"

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
    valid_from = models.DateTimeField()
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
                    | models.Q(valid_to__gt=models.F("valid_from"))
                ),
                name="ck_discount_valid_period",
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