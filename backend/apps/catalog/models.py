"""Модели приложения каталога."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.codes import generate_code
from apps.directory.characteristics.models import Characteristic, CharacteristicValue
from apps.directory.common.models import (
    Brand,
    Category,
    Color,
    Execution,
    Group,
    ProtectionDegree,
    Series,
    SupplyVariant,
    Type,
    TypeModel,
)


class Product(models.Model):
    prd_code = models.CharField(max_length=20, unique=True, editable=False)
    prd_article = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT, related_name="products", null=True, blank=True
    )
    series = models.ForeignKey(
        Series, on_delete=models.PROTECT, related_name="products", null=True, blank=True
    )
    type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name="products")
    type_model = models.ForeignKey(
        TypeModel,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    execution = models.ForeignKey(
        Execution,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    protection_degree = models.ForeignKey(
        ProtectionDegree,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    color = models.ForeignKey(
        Color, on_delete=models.PROTECT, related_name="products", null=True, blank=True
    )
    supply_variant = models.ForeignKey(
        SupplyVariant,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    prd_name = models.CharField(max_length=1024, blank=True)
    prd_description = models.TextField(blank=True)
    prd_notes = models.TextField(blank=True)
    status = models.BooleanField(default=True)
    product_image_1 = models.ImageField(upload_to="products/", null=True, blank=True)
    product_image_2 = models.ImageField(upload_to="products/", null=True, blank=True)
    product_image_3 = models.ImageField(upload_to="products/", null=True, blank=True)
    packaging = models.TextField(null=True, blank=True)
    sales_unit = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=255, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_product"
        ordering = ("prd_article",)

    def save(self, *args, **kwargs):
        if not self.prd_code:
            self.prd_code = generate_code(type(self), "prd_code", "prd")
        from apps.catalog.services.naming import ProductNameService

        ProductNameService.populate(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.prd_article


class ProductNameRule(models.Model):
    type = models.OneToOneField(
        Type, on_delete=models.CASCADE, related_name="product_name_rule"
    )

    class Meta:
        db_table = "catalog_product_name_rule"
        verbose_name = _("Product name rule")
        verbose_name_plural = _("Product name rules")

    def __str__(self):
        return str(self.type)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.refresh_product_names()

    def delete(self, *args, **kwargs):
        type_id = self.type_id
        result = super().delete(*args, **kwargs)
        Product.objects.filter(type_id=type_id).update(
            prd_name_en="Без названия",
            prd_name_ru="Без названия",
            prd_name_uk="Без названия",
        )
        return result

    def refresh_product_names(self):
        for product in Product.objects.filter(type_id=self.type_id).iterator():
            product.save(update_fields=("prd_name_en", "prd_name_ru", "prd_name_uk"))


class ProductNameRuleComponent(models.Model):
    COMPONENT_TYPE = "type"
    COMPONENT_MODEL = "model"
    COMPONENT_EXECUTION = "execution"
    COMPONENT_PROTECTION = "protection_degree"
    COMPONENT_CHARACTERISTICS = "characteristics"
    COMPONENT_COLOR = "color"
    COMPONENT_SUPPLY = "supply_variant"
    COMPONENT_CHOICES = (
        (COMPONENT_TYPE, _("Type")),
        (COMPONENT_MODEL, _("Model")),
        (COMPONENT_EXECUTION, _("Execution")),
        (COMPONENT_PROTECTION, _("Protection degree")),
        (COMPONENT_CHARACTERISTICS, _("Characteristics")),
        (COMPONENT_COLOR, _("Color")),
        (COMPONENT_SUPPLY, _("Supply variant")),
    )

    rule = models.ForeignKey(
        ProductNameRule, on_delete=models.CASCADE, related_name="components"
    )
    component = models.CharField(max_length=32, choices=COMPONENT_CHOICES)
    position = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "catalog_product_name_rule_component"
        ordering = ("position",)
        constraints = (
            models.UniqueConstraint(
                fields=("rule", "component"), name="uq_name_rule_component"
            ),
            models.UniqueConstraint(
                fields=("rule", "position"), name="uq_name_rule_position"
            ),
        )

    def __str__(self):
        return f"{self.rule}: {self.component} ({self.position})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.rule.refresh_product_names()

    def delete(self, *args, **kwargs):
        rule = self.rule
        result = super().delete(*args, **kwargs)
        rule.refresh_product_names()
        return result


class ProductCharacteristic(models.Model):
    VALUE_TYPE_CHOICES = (
        ("text", _("Text")),
        ("number", _("Number")),
        ("boolean", _("Boolean")),
        ("reference", _("Reference")),
    )

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="characteristics"
    )
    characteristic = models.ForeignKey(
        Characteristic, on_delete=models.PROTECT, related_name="product_characteristics"
    )
    value_type = models.CharField(
        max_length=20, choices=VALUE_TYPE_CHOICES, default="text"
    )
    value_text = models.TextField(null=True, blank=True)
    value_number = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    value_boolean = models.BooleanField(null=True, blank=True)
    value_reference = models.ForeignKey(
        CharacteristicValue,
        on_delete=models.PROTECT,
        related_name="product_characteristics",
        null=True,
        blank=True,
    )
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product_characteristic"
        constraints = (
            models.UniqueConstraint(
                fields=("product", "characteristic"), name="uq_product_characteristic"
            ),
        )

    def clean(self):
        field_by_type = {
            "text": self.value_text,
            "number": self.value_number,
            "boolean": self.value_boolean,
            "reference": self.value_reference_id,
        }
        expected = self.value_type
        if expected not in field_by_type:
            raise ValidationError(
                {"characteristic": "Unsupported characteristic value type."}
            )
        populated = [key for key, value in field_by_type.items() if value is not None]
        if populated != [expected]:
            raise ValidationError(
                {
                    "characteristic": f"Provide only the value matching type '{expected}'."
                }
            )
        if (
            expected == "reference"
            and self.value_reference_id
            and self.value_reference.cv_characteristic_id != self.characteristic_id
        ):
            raise ValidationError(
                {
                    "value_reference": "Reference must belong to the selected characteristic."
                }
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.save(update_fields=("prd_name_en", "prd_name_ru", "prd_name_uk"))

    def delete(self, *args, **kwargs):
        product = self.product
        result = super().delete(*args, **kwargs)
        product.save(update_fields=("prd_name_en", "prd_name_ru", "prd_name_uk"))
        return result
