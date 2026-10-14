from django.db import models
from django.utils.translation import gettext_lazy as _

from .services.codes import generate_code


# 1. Справочник категорий
class Category(models.Model):
    cat_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    cat_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    cat_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    cat_status = models.BooleanField(
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
        db_table = "common_category"
        ordering = ("cat_name",)
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        db_table_comment = "Общий справочник категорий продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["cat_name_en"],
                condition=~models.Q(cat_name_en=""),
                name="uq_category_name_en",
            ),
            models.UniqueConstraint(
                fields=["cat_name_ru"],
                condition=~models.Q(cat_name_ru=""),
                name="uq_category_name_ru",
            ),
            models.UniqueConstraint(
                fields=["cat_name_uk"],
                condition=~models.Q(cat_name_uk=""),
                name="uq_category_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.cat_code:
            self.cat_code = generate_code(
                Category,
                "cat_code",
                "cat",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.cat_name


# 2. Справочник групп
class Group(models.Model):
    grp_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    grp_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    grp_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    grp_status = models.BooleanField(
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
        db_table = "common_group"
        ordering = ("grp_name",)
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        db_table_comment = "Общий справочник групп продукции"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["grp_name_en"],
                condition=~models.Q(grp_name_en=""),
                name="uq_group_name_en",
            ),
            models.UniqueConstraint(
                fields=["grp_name_ru"],
                condition=~models.Q(grp_name_ru=""),
                name="uq_group_name_ru",
            ),
            models.UniqueConstraint(
                fields=["grp_name_uk"],
                condition=~models.Q(grp_name_uk=""),
                name="uq_group_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.grp_code:
            self.grp_code = generate_code(
                Group,
                "grp_code",
                "grp",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.grp_name


# 3. Справочник брендов
class Brand(models.Model):
    brd_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    brd_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    brd_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    brd_status = models.BooleanField(
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
        db_table = "common_brand"
        ordering = ("brd_name",)
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        db_table_comment = "Общий справочник брендов продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["brd_name_en"],
                condition=~models.Q(brd_name_en=""),
                name="uq_brand_name_en",
            ),
            models.UniqueConstraint(
                fields=["brd_name_ru"],
                condition=~models.Q(brd_name_ru=""),
                name="uq_brand_name_ru",
            ),
            models.UniqueConstraint(
                fields=["brd_name_uk"],
                condition=~models.Q(brd_name_uk=""),
                name="uq_brand_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.brd_code:
            self.brd_code = generate_code(
                Brand,
                "brd_code",
                "brd",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.brd_name


# 4. Справочник серий
class Series(models.Model):
    ser_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="series",
    )

    ser_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    ser_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    ser_status = models.BooleanField(
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
        db_table = "common_series"
        ordering = ("ser_name",)
        verbose_name = _("Series")
        verbose_name_plural = _("Series")
        db_table_comment = "Общий справочник серий продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["ser_name_en"],
                condition=~models.Q(ser_name_en=""),
                name="uq_series_name_en",
            ),
            models.UniqueConstraint(
                fields=["ser_name_ru"],
                condition=~models.Q(ser_name_ru=""),
                name="uq_series_name_ru",
            ),
            models.UniqueConstraint(
                fields=["ser_name_uk"],
                condition=~models.Q(ser_name_uk=""),
                name="uq_series_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.ser_code:
            self.ser_code = generate_code(
                Series,
                "ser_code",
                "ser",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ser_name


# 5. Справочник типов
class Type(models.Model):
    typ_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    typ_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    typ_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    typ_status = models.BooleanField(
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
        db_table = "common_type"
        ordering = ("typ_name",)
        verbose_name = _("Type")
        verbose_name_plural = _("Types")
        db_table_comment = "Общий справочник типов продукции"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["typ_name_en"],
                condition=~models.Q(typ_name_en=""),
                name="uq_type_name_en",
            ),
            models.UniqueConstraint(
                fields=["typ_name_ru"],
                condition=~models.Q(typ_name_ru=""),
                name="uq_type_name_ru",
            ),
            models.UniqueConstraint(
                fields=["typ_name_uk"],
                condition=~models.Q(typ_name_uk=""),
                name="uq_type_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.typ_code:
            self.typ_code = generate_code(
                Type,
                "typ_code",
                "typ",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.typ_name


# 6. Справочник степеней защиты
class ProtectionDegree(models.Model):
    ptd_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    ptd_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    ptd_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    ptd_status = models.BooleanField(
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
        db_table = "common_protection_degree"
        ordering = ("ptd_name",)
        verbose_name = _("Protection degree")
        verbose_name_plural = _("Protection degrees")
        db_table_comment = "Общий справочник степеней защиты продукции"

    def save(self, *args, **kwargs):
        if not self.ptd_code:
            self.ptd_code = generate_code(
                ProtectionDegree,
                "ptd_code",
                "ptd",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ptd_name


# 7. Справочник цветов
class Color(models.Model):
    clr_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    clr_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    clr_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    clr_status = models.BooleanField(
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
        db_table = "common_color"
        ordering = ("clr_name",)
        verbose_name = _("Color")
        verbose_name_plural = _("Colors")
        db_table_comment = "Общий справочник цветов продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["clr_name_en"],
                condition=~models.Q(clr_name_en=""),
                name="uq_color_name_en",
            ),
            models.UniqueConstraint(
                fields=["clr_name_ru"],
                condition=~models.Q(clr_name_ru=""),
                name="uq_color_name_ru",
            ),
            models.UniqueConstraint(
                fields=["clr_name_uk"],
                condition=~models.Q(clr_name_uk=""),
                name="uq_color_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.clr_code:
            self.clr_code = generate_code(
                Color,
                "clr_code",
                "clr",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.clr_name


# 8. Справочник моделей типов
class TypeModel(models.Model):
    mdl_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    mdl_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    mdl_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    mdl_status = models.BooleanField(
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
        db_table = "common_type_model"
        ordering = ("mdl_name",)
        verbose_name = _("Type model")
        verbose_name_plural = _("Type models")
        db_table_comment = "Общий справочник типов моделей продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["mdl_name_en"],
                condition=~models.Q(mdl_name_en=""),
                name="uq_type_model_name_en",
            ),
            models.UniqueConstraint(
                fields=["mdl_name_ru"],
                condition=~models.Q(mdl_name_ru=""),
                name="uq_type_model_name_ru",
            ),
            models.UniqueConstraint(
                fields=["mdl_name_uk"],
                condition=~models.Q(mdl_name_uk=""),
                name="uq_type_model_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.mdl_code:
            self.mdl_code = generate_code(
                TypeModel,
                "mdl_code",
                "mdl",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mdl_name


# 9. Справочник исполнений
class Execution(models.Model):
    exc_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    exc_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    exc_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    exc_status = models.BooleanField(
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
        db_table = "common_execution"
        ordering = ("exc_name",)
        verbose_name = _("Execution")
        verbose_name_plural = _("Executions")
        db_table_comment = "Общий справочник исполнений продукции"

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["exc_name_en"],
                condition=~models.Q(exc_name_en=""),
                name="uq_execution_name_en",
            ),
            models.UniqueConstraint(
                fields=["exc_name_ru"],
                condition=~models.Q(exc_name_ru=""),
                name="uq_execution_name_ru",
            ),
            models.UniqueConstraint(
                fields=["exc_name_uk"],
                condition=~models.Q(exc_name_uk=""),
                name="uq_execution_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.exc_code:
            self.exc_code = generate_code(
                Execution,
                "exc_code",
                "exc",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.exc_name


# 10. Справочник вариантов поставки
class SupplyVariant(models.Model):
    sup_code = models.CharField(
        _("Code"),
        max_length=20,
        unique=True,
        editable=False,
    )

    sup_name = models.CharField(
        _("Name"),
        max_length=255,
    )

    sup_description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )

    sup_status = models.BooleanField(
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
        db_table = "common_supply_variant"
        ordering = ("sup_name",)
        verbose_name = _("Supply variant")
        verbose_name_plural = _("Supply variants")
        db_table_comment = "Общий справочник вариантов поставки продукции"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["sup_name_en"],
                condition=~models.Q(sup_name_en=""),
                name="uq_supply_variant_name_en",
            ),
            models.UniqueConstraint(
                fields=["sup_name_ru"],
                condition=~models.Q(sup_name_ru=""),
                name="uq_supply_variant_name_ru",
            ),
            models.UniqueConstraint(
                fields=["sup_name_uk"],
                condition=~models.Q(sup_name_uk=""),
                name="uq_supply_variant_name_uk",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.sup_code:
            self.sup_code = generate_code(
                SupplyVariant,
                "sup_code",
                "sup",
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sup_name

