from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.codes import generate_code

# Справочник групп характеристик
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
        db_table_comment = "Справочник групп характеристик"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("chg_name_en",),
                condition=~Q(chg_name_en=""),
                name="uq_characteristic_group_name_en",
            ),
            models.UniqueConstraint(
                fields=("chg_name_ru",),
                condition=~Q(chg_name_ru=""),
                name="uq_characteristic_group_name_ru",
            ),
            models.UniqueConstraint(
                fields=("chg_name_uk",),
                condition=~Q(chg_name_uk=""),
                name="uq_characteristic_group_name_uk",
            ),
        ]

        

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
        blank=True,
        null=True,
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
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("unt_name_en",),
                condition=~Q(unt_name_en=""),
                name="uq_unit_name_en",
            ),
            models.UniqueConstraint(
                fields=("unt_name_ru",),
                condition=~Q(unt_name_ru=""),
                name="uq_unit_name_ru",
            ),
            models.UniqueConstraint(
                fields=("unt_name_uk",),
                condition=~Q(unt_name_uk=""),
                name="uq_unit_name_uk",
            ),
        ]

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
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("chr_name_en",),
                condition=~Q(chr_name_en=""),
                name="uq_characteristic_name_en",
            ),
            models.UniqueConstraint(
                fields=("chr_name_ru",),
                condition=~Q(chr_name_ru=""),
                name="uq_characteristic_name_ru",
            ),
            models.UniqueConstraint(
                fields=("chr_name_uk",),
                condition=~Q(chr_name_uk=""),
                name="uq_characteristic_name_uk",
            ),
        ]

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

# Справочник значений характеристик продукции

class CharacteristicValue(models.Model):
    cv_code = models.CharField(
    _("Code"),
    max_length=20,
    unique=True,
    editable=False,
    )


    cv_characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.PROTECT,
        related_name="values",
        verbose_name=_("Characteristic"),
    )

    cv_value = models.CharField(
        _("Value"),
        max_length=255,
    )

    cv_description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
    )

    cv_status = models.BooleanField(
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
        db_table = "characteristics_value"
        ordering = ("cv_characteristic", "cv_value") 
        verbose_name = _("Characteristic value")
        verbose_name_plural = _("Characteristic values")
        db_table_comment = "Справочник значений характеристик продукции"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("cv_characteristic", "cv_value"),
                name="uq_characteristic_value",
            ),
        ]

    def __str__(self):
        return f"{self.cv_characteristic}: {self.cv_value}"

    def save(self, *args, **kwargs):
        if not self.cv_code:
            self.cv_code = generate_code(
                self.__class__,
                "cv_code",
                "cv",
            )
        super().save(*args, **kwargs)

