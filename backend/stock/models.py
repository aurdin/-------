from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Warehouse(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Код",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения",
    )

    class Meta:
        db_table = "stock_warehouse"
        ordering = ("name",)
        verbose_name = "Склад"
        verbose_name_plural = "Склады"

    def __str__(self):
        return f"{self.code} — {self.name}"


class StockPolicy(models.Model):
    low_stock_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name="Порог малого остатка",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения",
    )

    class Meta:
        db_table = "stock_policy"
        verbose_name = "Политика остатков"
        verbose_name_plural = "Политики остатков"

    def __str__(self):
        return f"Порог малого остатка: {self.low_stock_threshold}"


class Stock(models.Model):
    class Status(models.TextChoices):
        IN_STOCK = "IN_STOCK", "В наличии"
        LOW_STOCK = "LOW_STOCK", "Мало"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Нет в наличии"
        ON_ORDER = "ON_ORDER", "Под заказ"
        DISCONTINUED = "DISCONTINUED", "Снят с продажи"

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stocks",
        verbose_name="Товар",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stocks",
        verbose_name="Склад",
    )
    quantity_available = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Доступно",
    )

    quantity_reserved = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Зарезервировано",
    )

    quantity_incoming = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Ожидается",
    )

    quantity_on_order = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Заказано поставщику",
    )

    is_discontinued = models.BooleanField(
        default=False,
        verbose_name="Снят с продажи",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OUT_OF_STOCK,
        verbose_name="Статус",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения",
    )

    class Meta:
        db_table = "stock_stock"
        ordering = ("product", "warehouse",)
        verbose_name = "Остаток"
        verbose_name_plural = "Остатки"
        constraints = (
            models.UniqueConstraint(
                fields=("product", "warehouse",),
                name="unique_product_warehouse_stock",
            ),
        )

    def __str__(self):
        return f"{self.product} — {self.warehouse}"
