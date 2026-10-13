"""Модели связей между общими справочниками SmEl."""
from django.db import models
from django.utils.translation import gettext_lazy as _


# 1. Связь групп и типов
class GroupType(models.Model):
    group = models.ForeignKey(
        "common.Group",
        on_delete=models.PROTECT,
        related_name="group_types",
    )

    type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        related_name="group_types",
    )

    class Meta:
        db_table = "relations_group_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("group", "type"),
                name="unique_group_type",
            ),
        ]
        verbose_name = _("Group type")
        verbose_name_plural = _("Group types")
        db_table_comment = "Связь групп и типов продукции"

    def __str__(self):
        return f"{self.group} — {self.type}"


# 2. Связь серии и типа
class SeriesType(models.Model):
    series = models.ForeignKey(
        "common.Series",
        on_delete=models.PROTECT,
        related_name="series_types",
    )

    type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        related_name="series_types",
    )

    class Meta:
        db_table = "relations_series_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "type"),
                name="unique_series_type",
            ),
        ]
        verbose_name = _("Series type")
        verbose_name_plural = _("Series types")
        db_table_comment = "Связь серий и типов продукции"

    def __str__(self):
        return f"{self.series} — {self.type}"


# 3. Цвета товаров серии
class SeriesProductColor(models.Model):
    series = models.ForeignKey(
        "common.Series",
        on_delete=models.PROTECT,
        related_name="product_colors",
    )

    color = models.ForeignKey(
        "common.Color",
        on_delete=models.PROTECT,
        related_name="product_series",
    )

    class Meta:
        db_table = "relations_series_product_color"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "color"),
                name="unique_series_product_color",
            ),
        ]
        verbose_name = _("Series product color")
        verbose_name_plural = _("Series product colors")
        db_table_comment = "Связь серий и цветов продукции"

    def __str__(self):
        return f"{self.series} — {self.color}"


# 4. Цвета рамок серии
class SeriesFrameColor(models.Model):
    series = models.ForeignKey(
        "common.Series",
        on_delete=models.PROTECT,
        related_name="frame_colors",
    )

    color = models.ForeignKey(
        "common.Color",
        on_delete=models.PROTECT,
        related_name="frame_series",
    )

    class Meta:
        db_table = "relations_series_frame_color"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("series", "color"),
                name="unique_series_frame_color",
            ),
        ]
        verbose_name = _("Series frame color")
        verbose_name_plural = _("Series frame colors")
        db_table_comment = "Связь серий и цветов рамок продукции"

    def __str__(self):
        return f"{self.series} — {self.color}"


# 5. Связь типов и моделей
class TypeModelType(models.Model):
    type_model = models.ForeignKey(
        "common.TypeModel",
        on_delete=models.PROTECT,
        related_name="type_links",
    )

    type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        related_name="model_links",
    )

    class Meta:
        db_table = "relations_type_model_type"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("type_model", "type"),
                name="unique_type_model_type",
            ),
        ]
        verbose_name = _("Type model type")
        verbose_name_plural = _("Type model types")
        db_table_comment = "Связь типов и моделей продукции"

    def __str__(self):
        return f"{self.type_model} — {self.type}"


# 6. Связь типов и исполнений
class TypeExecution(models.Model):
    type = models.ForeignKey(
        "common.Type",
        on_delete=models.PROTECT,
        related_name="execution_links",
    )

    execution = models.ForeignKey(
        "common.Execution",
        on_delete=models.PROTECT,
        related_name="type_links",
    )

    class Meta:
        db_table = "relations_type_execution"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("type", "execution"),
                name="unique_type_execution",
            ),
        ]
        verbose_name = _("Type execution")
        verbose_name_plural = _("Type executions")
        db_table_comment = "Связь типов и исполнений продукции"

    def __str__(self):
        return f"{self.type} — {self.execution}"

