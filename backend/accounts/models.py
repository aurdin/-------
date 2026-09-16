from django.conf import settings
from django.db import models
from django.db.models import Q


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"CustomerProfile #{self.pk} — {self.user.username}"


class CustomerAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_addresses",
    )
    title = models.CharField(
        max_length=100,
        blank=True,
    )
    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
    )
    phone = models.CharField(
        max_length=30,
    )
    country = models.CharField(
        max_length=100,
    )
    region = models.CharField(
        max_length=150,
        blank=True,
    )
    city = models.CharField(
        max_length=150,
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )
    address_line = models.CharField(
        max_length=255,
    )
    apartment = models.CharField(
        max_length=50,
        blank=True,
    )
    is_default = models.BooleanField(
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(is_default=True),
                name="uq_customer_default_address",
            ),
        )

    def __str__(self):
        if self.title:
            return f"{self.title} — {self.user.username}"

        return f"CustomerAddress #{self.pk} — {self.user.username}"
