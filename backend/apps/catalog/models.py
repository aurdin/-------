"""Модели приложения каталога."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.codes import generate_code
from apps.directory.characteristics.models import Characteristic, CharacteristicValue, Unit
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
    prd_code = models.CharField(
        _("Code"), max_length=20, unique=True, editable=False
    )
    prd_article = models.CharField(_("Article"), max_length=255, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("Category")
    )
    group = models.ForeignKey(
        Group, on_delete=models.PROTECT, related_name="products", verbose_name=_("Group")
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Brand"),
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Series"),
    )
    type = models.ForeignKey(
        Type, on_delete=models.PROTECT, related_name="products", verbose_name=_("Type")
    )
    type_model = models.ForeignKey(
        TypeModel,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Type model"),
    )
    execution = models.ForeignKey(
        Execution,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Execution"),
    )
    protection_degree = models.ForeignKey(
        ProtectionDegree,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Protection degree"),
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Color"),
    )
    supply_variant = models.ForeignKey(
        SupplyVariant,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Supply variant"),
    )
    prd_name = models.CharField(_("Name"), max_length=1024, blank=True)
    prd_description = models.TextField(_("Description"), blank=True)
    prd_characteristics = models.TextField(_("Characteristics"), blank=True)
    prd_notes = models.TextField(_("Notes"), blank=True)
    status = models.BooleanField(_("Status"), default=True)
    product_image_1 = models.ImageField(_("Product photo 1"), upload_to="products/", null=True, blank=True)
    product_image_2 = models.ImageField(_("Product photo 2"), upload_to="products/", null=True, blank=True)
    product_image_3 = models.ImageField(_("Product photo 3"), upload_to="products/", null=True, blank=True)
    packaging = models.TextField(_("Packaging"), null=True, blank=True)
    sales_unit = models.CharField(_("Sales unit"), max_length=50, blank=True)
    barcode = models.CharField(_("Barcode"), max_length=255, null=True, blank=True)
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        db_table = "catalog_product"
        ordering = ("prd_article",)
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def save(self, *args, **kwargs):
        if not self.prd_code:
            self.prd_code = generate_code(type(self), "prd_code", "prd")
        from apps.catalog.services.naming import ProductNameService
        from apps.catalog.services.descriptions import ProductDescriptionService
        from apps.catalog.services.product_characteristics import (
            ProductCharacteristicsService,
        )

        ProductNameService.populate(self)
        ProductDescriptionService.populate(self)
        ProductCharacteristicsService.populate(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.prd_article


class ProductNameRule(models.Model):
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="product_name_rule",
        verbose_name=_("Group"),
    )

    class Meta:
        db_table = "catalog_product_name_rule"
        verbose_name = _("Product name rule")
        verbose_name_plural = _("Product name rules")

    def __str__(self):
        return str(self.group)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.refresh_product_names()

    def delete(self, *args, **kwargs):
        group_id = self.group_id
        result = super().delete(*args, **kwargs)
        Product.objects.filter(group_id=group_id).update(
            prd_name_en="Без названия",
            prd_name_ru="Без названия",
            prd_name_uk="Без названия",
        )
        return result

    def refresh_product_names(self):
        for product in Product.objects.filter(group_id=self.group_id).iterator():
            product.save(update_fields=("prd_name_en", "prd_name_ru", "prd_name_uk"))


class ProductNameRuleComponent(models.Model):
    COMPONENT_TYPE = "type"
    COMPONENT_MODEL = "model"
    COMPONENT_EXECUTION = "execution"
    COMPONENT_PROTECTION = "protection_degree"
    COMPONENT_COLOR = "color"
    COMPONENT_SUPPLY = "supply_variant"
    COMPONENT_CHOICES = (
        (COMPONENT_TYPE, _("Type")),
        (COMPONENT_MODEL, _("Model")),
        (COMPONENT_EXECUTION, _("Execution")),
        (COMPONENT_PROTECTION, _("Protection degree")),
        (COMPONENT_COLOR, _("Color")),
        (COMPONENT_SUPPLY, _("Supply variant")),
    )

    rule = models.ForeignKey(
        ProductNameRule, on_delete=models.CASCADE, related_name="components"
    )
    component = models.CharField(
        max_length=32,
        choices=COMPONENT_CHOICES,
        blank=True,
        verbose_name=_("Component"),
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.PROTECT,
        related_name="product_name_rule_components",
        null=True,
        blank=True,
        verbose_name=_("Characteristic"),
    )

    position = models.PositiveSmallIntegerField(verbose_name=_("Position"))

    class Meta:
        db_table = "catalog_product_name_rule_component"
        verbose_name = _("Product name rule item")
        verbose_name_plural = _("Product name rule items")
        constraints = (
            models.UniqueConstraint(
                fields=("rule", "component"),
                condition=~models.Q(component=""),
                name="uq_name_rule_component",
            ),
            models.UniqueConstraint(
                fields=("rule", "position"), name="uq_name_rule_position"
            ),
            models.UniqueConstraint(
                fields=("rule", "characteristic"),
                condition=models.Q(characteristic__isnull=False),
                name="uq_name_rule_characteristic",
            ),
        )

    def clean(self):
        super().clean()
        if bool(self.component) == bool(self.characteristic_id):
            raise ValidationError(
                {"component": _("Select either a standard component or a characteristic.")}
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
    VALUE_TYPE_CHOICES = Characteristic.VALUE_TYPE_CHOICES

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="characteristics"
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.PROTECT,
        related_name="product_characteristics",
        verbose_name=_("Characteristic"),
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="product_characteristics",
        null=True,
        blank=True,
        verbose_name=_("Unit"),
    )
    value_type = models.CharField(
        max_length=20,
        choices=VALUE_TYPE_CHOICES,
        default=Characteristic.VALUE_TYPE_TEXT,
        editable=False,
    )
    value_text = models.TextField(_("Value"), null=True, blank=True)
    value_number = models.DecimalField(
        _("Value"), max_digits=20, decimal_places=6, null=True, blank=True
    )
    value_boolean = models.BooleanField(_("Value"), null=True, blank=True)
    value_reference = models.ForeignKey(
        CharacteristicValue,
        on_delete=models.PROTECT,
        related_name="product_characteristics",
        null=True,
        blank=True,
        verbose_name=_("Value"),
    )
    status = models.BooleanField(_("Status"), default=True)

    class Meta:
        db_table = "catalog_product_characteristic"
        verbose_name = _("Product characteristic")
        verbose_name_plural = _("Product characteristics")
        constraints = (
            models.UniqueConstraint(
                fields=("product", "characteristic"), name="uq_product_characteristic"
            ),
        )

    def __str__(self):
        return ""

    def clean(self):
        field_by_type = {
            "text": self.value_text,
            "number": self.value_number,
            "boolean": self.value_boolean,
            "reference": self.value_reference_id,
        }
        expected = (
            self.characteristic.chr_value_type
            if self.characteristic_id
            else None
        )
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
        if self.characteristic_id:
            self.value_type = self.characteristic.chr_value_type
        super().save(*args, **kwargs)
        self.product.save(update_fields=self.product_generated_fields())

    def delete(self, *args, **kwargs):
        product = self.product
        result = super().delete(*args, **kwargs)
        product.save(update_fields=self.product_generated_fields())
        return result

    @staticmethod
    def product_generated_fields():
        languages = ("en", "ru", "uk")
        return tuple(
            f"prd_{field}_{language}"
            for field in ("name", "characteristics")
            for language in languages
        )
