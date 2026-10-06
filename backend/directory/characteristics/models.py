from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.codes import generate_code


class CharacteristicGroup(models.Model):
    chg_code = models.CharField(
    _("Code"),
    max_length=20,
    unique=True,
    editable=False,
    )

    chg_name = models.CharField(
        _("Name"),
        max_length=255,
        blank=True,
    )

    chg_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    chg_status = models.BooleanField(
        _("Status"),
        default=True,
    )

    date_created = models.DateTimeField(
        _("Date created"),
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        _("Date updated"),
        auto_now=True,
    )

    class Meta:
        db_table = "characteristics_group"
        ordering = ["chg_name"]  # noqa: RUF012
        verbose_name = _("Characteristic group")
        verbose_name_plural = _("Characteristic groups")

    def __str__(self):
        return self.chg_name

    def save(self, *args, **kwargs):
        if not self.chg_code:
            self.chg_code = generate_code(
                self.__class__,
                "chg_code",
                "chg",
            )
        super().save(*args, **kwargs)


# Справочник единиц измерения
class Unit(models.Model):
    unt_code = models.CharField(
    _("Code"),
    max_length=20,
    unique=True,
    editable=False,
)

    unt_name = models.CharField(
        _("Name"),
        max_length=255,
        blank=True,
    )

    unt_symbol = models.CharField(
        _("Symbol"),
        max_length=20,
    )

    unt_status = models.BooleanField(
        _("Status"),
        default=True,
    )

    date_created = models.DateTimeField(
        _("Date created"),
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        _("Date updated"),
        auto_now=True,
    )

    class Meta:
        db_table = "characteristics_unit"
        ordering = ["unt_name"]  # noqa: RUF012
        verbose_name = _("Unit")
        verbose_name_plural = _("Units")

    def __str__(self):
        return self.unt_name

    def save(self, *args, **kwargs):
        if not self.unt_code:
            self.unt_code = generate_code(
                self.__class__,
                "unt_code",
                "unt",
            )
        super().save(*args, **kwargs)        
