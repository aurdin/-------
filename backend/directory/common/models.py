from django.db import models
from django.utils.translation import gettext_lazy as _

from .services.codes import generate_code


# Справочник категорий
class Category(models.Model):
    cat_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    cat_name = models.CharField(
        max_length=255,
    )

    cat_description = models.TextField(
        null=True,
        blank=True,
    )

    cat_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_category"
        ordering = ("cat_name",)
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def save(self, *args, **kwargs):
        if not self.cat_code:
            self.cat_code = generate_code(Category, "cat_code", "cat")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.cat_name


# Справочник групп
class Group(models.Model):
    grp_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    grp_name = models.CharField(
        max_length=255,
    )

    grp_description = models.TextField(
        null=True,
        blank=True,
    )

    grp_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_group"
        ordering = ("grp_name",)
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    def save(self, *args, **kwargs):
        if not self.grp_code:
            self.grp_code = generate_code(Group, "grp_code", "grp")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.grp_name

# Справочник брендов
class Brand(models.Model):
    brd_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    brd_name = models.CharField(
        max_length=255,
    )

    brd_description = models.TextField(
        null=True,
        blank=True,
    )

    brd_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_brand"
        ordering = ("brd_name",)
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")

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


# Справочник серий
class Series(models.Model):
    ser_code = models.CharField(
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
        max_length=255,
    )

    ser_description = models.TextField(
        null=True,
        blank=True,
    )

    ser_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_series"
        ordering = ("ser_name",)
        verbose_name = _("Series")
        verbose_name_plural = _("Series")

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


# Справочник типов
class Type(models.Model):
    typ_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    typ_name = models.CharField(
        max_length=255,
    )

    typ_description = models.TextField(
        null=True,
        blank=True,
    )

    typ_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_type"
        ordering = ("typ_name",)
        verbose_name = _("Type")
        verbose_name_plural = _("Types")

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


# Связь групп и типов
class GroupType(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="group_types",
    )

    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        related_name="group_types",
    )

    class Meta:
        db_table = "common_group_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("group", "type"),
                name="unique_group_type",
            ),
        ]
        verbose_name = _("Group type")
        verbose_name_plural = _("Group types")

    def __str__(self):
        return f"{self.group} — {self.type}"


# Связь серии и типа
class SeriesType(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="series_types",
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        related_name="series_types",
    )

    class Meta:
        db_table = "common_series_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "type"),
                name="unique_series_type",
            ),
        ]
        verbose_name = _("Series type")
        verbose_name_plural = _("Series types")

    def __str__(self):
        return f"{self.series} — {self.type}"


# Справочник степеней защиты
class ProtectionDegree(models.Model):
    ptd_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    ptd_name = models.CharField(max_length=255)
    ptd_description = models.TextField(null=True, blank=True)
    ptd_status = models.BooleanField(default=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "common_protection_degree"
        ordering = ("ptd_name",)
        verbose_name = _("Protection degree")
        verbose_name_plural = _("Protection degrees")

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


# Справочник цветов
class Color(models.Model):
    clr_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    clr_name = models.CharField(
        max_length=255,
    )

    clr_description = models.TextField(
        null=True,
        blank=True,
    )

    clr_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_color"
        ordering = ("clr_name",)
        verbose_name = _("Color")
        verbose_name_plural = _("Colors")

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


class SeriesProductColor(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="product_colors",
    )

    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="product_series",
    )

    class Meta:
        db_table = "common_series_product_color"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "color"),
                name="unique_series_product_color",
            ),
        ]
        verbose_name = _("Series product color")
        verbose_name_plural = _("Series product colors")

    def __str__(self):
        return f"{self.series} — {self.color}"   


# Цвета рамок серии
class SeriesFrameColor(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="frame_colors",
    )

    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="frame_series",
    )

    class Meta:
        db_table = "common_series_frame_color"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "color"),
                name="unique_series_frame_color",
            ),
        ]
        verbose_name = _("Series frame color")
        verbose_name_plural = _("Series frame colors")

    def __str__(self):
        return f"{self.series} — {self.color}"


# Справочник моделей типов
class TypeModel(models.Model):
    mdl_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    mdl_name = models.CharField(
        max_length=255,
    )

    mdl_description = models.TextField(
        null=True,
        blank=True,
    )

    mdl_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_type_model"
        ordering = ("mdl_name",)
        verbose_name = _("Type model")
        verbose_name_plural = _("Type models")

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


# Связь типов и моделей
class TypeModelType(models.Model):
    type_model = models.ForeignKey(
        TypeModel,
        on_delete=models.PROTECT,
        related_name="type_links",
    )

    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        related_name="model_links",
    )

    class Meta:
        db_table = "common_type_model_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("type_model", "type"),
                name="unique_type_model_type",
            ),
        ]
        verbose_name = _("Type model type")
        verbose_name_plural = _("Type model types")

    def __str__(self):
        return f"{self.type_model} — {self.type}"


# Справочник исполнений
class Execution(models.Model):
    exc_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    exc_name = models.CharField(
        max_length=255,
    )

    exc_description = models.TextField(
        null=True,
        blank=True,
    )

    exc_status = models.BooleanField(
        default=True,
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "common_execution"
        ordering = ("exc_name",)
        verbose_name = _("Execution")
        verbose_name_plural = _("Executions")

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


# Связь типов и исполнений
class TypeExecution(models.Model):
    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        related_name="execution_links",
    )

    execution = models.ForeignKey(
        Execution,
        on_delete=models.PROTECT,
        related_name="type_links",
    )

    class Meta:
        db_table = "common_type_execution"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("type", "execution"),
                name="unique_type_execution",
            ),
        ]
        verbose_name = _("Type execution")
        verbose_name_plural = _("Type executions")

    def __str__(self):
        return f"{self.type} — {self.execution}"