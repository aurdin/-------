from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.codes import generate_code

# Справочник привязки характеристик к группам продукции
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
        db_table_comment = _("Справочник привязки характеристик к группам продукции")

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
        db_table_comment = "Справочник единиц измерения"

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

# Справочник характеристик продукции
class Characteristic(models.Model):
    chr_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )
    chr_name = models.CharField(
        _("Name"),
        max_length=255,
        blank=True,
    )
    chr_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )
    chr_group = models.ForeignKey(
        CharacteristicGroup,
        on_delete=models.PROTECT,
        related_name="characteristics",
        verbose_name=_("Characteristic group"),
    )
    chr_unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="characteristics",
        verbose_name=_("Unit"),
        null=True,
        blank=True,
    )
    chr_status = models.BooleanField(
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
        db_table = "characteristics"
        ordering = ["chr_name"]  # noqa: RUF012
        verbose_name = _("Characteristic")
        verbose_name_plural = _("Characteristics")
        db_table_comment = "Справочник характеристик продукции"

    def __str__(self):
        return self.chr_name

    def save(self, *args, **kwargs):
        if not self.chr_code:
            self.chr_code = generate_code(
                self.__class__,
                "chr_code",
                "chr",
            )
        super().save(*args, **kwargs)

# Справочник типов характеристик продукции
class TypeCharacteristic(models.Model):
    tch_type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        related_name="type_characteristics",
        verbose_name=_("Type"),
    )
    tch_characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.PROTECT,
        related_name="type_characteristics",
        verbose_name=_("Characteristic"),
    )
    tch_status = models.BooleanField(
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
        db_table = "type_characteristics"
        ordering = ["tch_type", "tch_characteristic"]  # noqa: RUF012
        verbose_name = _("Type characteristic")
        verbose_name_plural = _("Type characteristics")
        db_table_comment = "Справочник типов характеристик продукции"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("tch_type", "tch_characteristic"),
                name="unique_type_characteristic",
            ),
        ]

    def __str__(self):
        return f"{self.tch_type} — {self.tch_characteristic}"                       
