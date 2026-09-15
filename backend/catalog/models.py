from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from catalog.services.color_availability import ColorAvailabilityService


def validate_characteristic_value(instance):
    characteristic = instance.characteristic
    value_type = characteristic.value_type

    value_fields = {
        "text": instance.value_text,
        "number": instance.value_number,
        "boolean": instance.value_boolean,
        "reference": instance.value_reference_id,
    }

    if value_type not in value_fields:
        raise ValidationError(
            {
                "characteristic": (
                    f"Unsupported characteristic value type: {value_type}."
                )
            }
        )

    populated_fields = [
        field_name for field_name, value in value_fields.items() if value is not None
    ]

    if len(populated_fields) != 1 or populated_fields[0] != value_type:
        raise ValidationError(
            {
                "characteristic": (
                    f"Value must be provided only in the field "
                    f"corresponding to value_type='{value_type}'."
                )
            }
        )

    if value_type == "reference" and instance.value_reference_id:
        if not CharacteristicValue.objects.filter(
            id=instance.value_reference_id,
            characteristic_id=instance.characteristic_id,
        ).exists():
            raise ValidationError(
                {
                    "value_reference": (
                        "Reference value must belong to the same Characteristic."
                    )
                }
            )


class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_category"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_group"
        ordering = ("name",)

    def __str__(self):
        return self.name


class CategoryGroup(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_groups",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="category_groups",
    )

    class Meta:
        db_table = "catalog_category_group"
        constraints = (
            models.UniqueConstraint(
                fields=("category", "group"),
                name="uq_category_group",
            ),
        )

    def __str__(self):
        return f"{self.category} — {self.group}"


class Brand(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_brand"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Series(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="series",
    )
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_series"
        ordering = ("name",)

    def __str__(self):
        return f"{self.brand} — {self.name}"


class Type(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_type"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Model(models.Model):
    type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        related_name="models",
    )
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_model"
        ordering = ("name",)

    def __str__(self):
        return f"{self.type} — {self.name}"


class Execution(models.Model):
    type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "catalog_execution"
        ordering = ("name",)

    def __str__(self):
        return f"{self.type} — {self.name}"
    
class Color(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TypeColor(models.Model):
    type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        related_name="type_colors",
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="type_colors",
    )
    status = models.BooleanField(default=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("type", "color",),
                name="uq_type_color",
            ),
        )

    def __str__(self):
        return f"{self.type} — {self.color}"


class SeriesColor(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="series_colors",
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="series_colors",
    )
    status = models.BooleanField(default=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("series", "color",),
                name="uq_series_color",
            ),
        )

    def __str__(self):
        return f"{self.series} — {self.color}"    


class Product(models.Model):
    article = models.CharField(
        max_length=255,
        unique=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="products",
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    series = models.ForeignKey(
        Series,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        related_name="products",
    )

    model = models.ForeignKey(
        Model,
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

    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    protection_degree = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    packaging = models.TextField(
        null=True,
        blank=True,
    )

    sales_unit = models.CharField(
        max_length=50,
    )
   
    barcode = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    manufacturer_name = models.TextField(
        null=True,
        blank=True,
    )

    manufacturer_description = models.TextField(
        null=True,
        blank=True,
    )

    status = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "catalog_product"
       
def clean(self):
    errors = {}

    if self.model_id and self.type_id and self.model.type_id != self.type_id:
        errors["model"] = "Model must belong to the same Type as Product."

    if (
        self.execution_id
        and self.type_id
        and self.execution.type_id != self.type_id
    ):
        errors["execution"] = "Execution must belong to the same Type as Product."

    if self.series_id:
        if not self.brand_id:
            errors["series"] = "Series cannot be specified without Brand."
        elif self.series.brand_id != self.brand_id:
            errors["series"] = "Series must belong to the same Brand as Product."

    if self.category_id and self.group_id:
        allowed = CategoryGroup.objects.filter(
            category_id=self.category_id,
            group_id=self.group_id,
        ).exists()

        if not allowed:
            errors["group"] = "The Category + Group combination is not allowed."

    if self.color_id and self.type_id:
        if not ColorAvailabilityService.is_allowed(
            self.type,
            self.series if self.series_id else None,
            self.color,
        ):
            errors["color"] = (
                "Color is not allowed for the selected Type and Series."
            )

    if errors:
        raise ValidationError(errors)
    
    def clean(self):
        errors = {}

        if self.model_id and self.type_id and self.model.type_id != self.type_id:
            errors["model"] = "Model must belong to the same Type as Product."

        if (
            self.execution_id
            and self.type_id
            and self.execution.type_id != self.type_id
        ):
            errors["execution"] = "Execution must belong to the same Type as Product."

        if self.series_id:
            if not self.brand_id:
                errors["series"] = "Series cannot be specified without Brand."
            elif self.series.brand_id != self.brand_id:
                errors["series"] = "Series must belong to the same Brand as Product."

        if self.category_id and self.group_id:
            allowed = CategoryGroup.objects.filter(
                category_id=self.category_id,
                group_id=self.group_id,
            ).exists()

            if not allowed:
                errors["group"] = "The Category + Group combination is not allowed."

        if self.color_id and self.type_id:
            if not ColorAvailabilityService.is_allowed(
                self.type,
                self.series if self.series_id else None,
                self.color,
            ):
                errors["color"] = (
                    "Color is not allowed for the selected Type and Series."
                )

        if errors:
            raise ValidationError(errors)    

    def __str__(self):
        return self.article


class Characteristic(models.Model):
    VALUE_TYPE_REFERENCE = "reference"
    VALUE_TYPE_NUMBER = "number"
    VALUE_TYPE_BOOLEAN = "boolean"
    VALUE_TYPE_TEXT = "text"

    VALUE_TYPE_CHOICES = (
        (VALUE_TYPE_REFERENCE, "Reference"),
        (VALUE_TYPE_NUMBER, "Number"),
        (VALUE_TYPE_BOOLEAN, "Boolean"),
        (VALUE_TYPE_TEXT, "Text"),
    )

    name = models.CharField(max_length=255)

    value_type = models.CharField(
        max_length=20,
        choices=VALUE_TYPE_CHOICES,
    )

    unit = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalog_characteristic"
        ordering = ("name",)

    def __str__(self):
        return self.name


class CharacteristicValue(models.Model):
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.CharField(max_length=255)
    description = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalog_characteristic_value"
        constraints = (
            models.UniqueConstraint(
                fields=("characteristic", "value"),
                name="uq_characteristic_value",
            ),
        )
        ordering = ("characteristic", "value")

    def __str__(self):
        return f"{self.characteristic}: {self.value}"


class TypeCharacteristic(models.Model):
    type = models.ForeignKey(
        Type,
        on_delete=models.CASCADE,
        related_name="characteristics",
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.CASCADE,
        related_name="type_characteristics",
    )

    value_text = models.TextField(
        null=True,
        blank=True,
    )
    value_number = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
    )
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
    )
    value_reference = models.ForeignKey(
        CharacteristicValue,
        on_delete=models.PROTECT,
        related_name="type_characteristics",
        null=True,
        blank=True,
    )

    status = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_type_characteristic"
        constraints = (
            models.UniqueConstraint(
                fields=("type", "characteristic"),
                name="uq_type_characteristic",
            ),
        )

    def clean(self):
        validate_characteristic_value(self)

    def __str__(self):
        return f"{self.type} — {self.characteristic}"


class ModelCharacteristic(models.Model):
    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        related_name="characteristics",
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.CASCADE,
        related_name="model_characteristics",
    )

    value_text = models.TextField(
        null=True,
        blank=True,
    )
    value_number = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
    )
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
    )
    value_reference = models.ForeignKey(
        CharacteristicValue,
        on_delete=models.PROTECT,
        related_name="model_characteristics",
        null=True,
        blank=True,
    )

    status = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_model_characteristic"
        constraints = (
            models.UniqueConstraint(
                fields=("model", "characteristic"),
                name="uq_model_characteristic",
            ),
        )

    def clean(self):
        if self.model_id and self.characteristic_id:
            if not TypeCharacteristic.objects.filter(
                type_id=self.model.type_id,
                characteristic_id=self.characteristic_id,
            ).exists():
                raise ValidationError(
                    {
                        "characteristic": (
                            "Characteristic is not allowed for the Model's Type."
                        )
                    }
                )

        validate_characteristic_value(self)

    def __str__(self):
        return f"{self.model} — {self.characteristic}"


class ExecutionCharacteristic(models.Model):
    execution = models.ForeignKey(
        Execution,
        on_delete=models.CASCADE,
        related_name="characteristics",
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.CASCADE,
        related_name="execution_characteristics",
    )

    value_text = models.TextField(
        null=True,
        blank=True,
    )
    value_number = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
    )
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
    )
    value_reference = models.ForeignKey(
        CharacteristicValue,
        on_delete=models.PROTECT,
        related_name="execution_characteristics",
        null=True,
        blank=True,
    )

    status = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_execution_characteristic"
        constraints = (
            models.UniqueConstraint(
                fields=("execution", "characteristic"),
                name="uq_execution_characteristic",
            ),
        )

    def clean(self):
        if self.execution_id and self.characteristic_id:
            if not TypeCharacteristic.objects.filter(
            type_id=self.execution.type_id,
            characteristic_id=self.characteristic_id,
        ).exists():
                raise ValidationError(
                {
                    "characteristic": (
                        "Characteristic is not allowed for "
                        "the Execution's Type."
                    )
                }
            )

        validate_characteristic_value(self)

    def __str__(self):
        return f"{self.execution} — {self.characteristic}"


class ProductCharacteristic(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="characteristics",
    )
    characteristic = models.ForeignKey(
        Characteristic,
        on_delete=models.CASCADE,
        related_name="product_characteristics",
    )

    value_text = models.TextField(
        null=True,
        blank=True,
    )
    value_number = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
    )
    value_boolean = models.BooleanField(
        null=True,
        blank=True,
    )
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
                fields=("product", "characteristic"),
                name="uq_product_characteristic",
            ),
        )

    def clean(self):
        if self.product_id and self.characteristic_id:
            if not TypeCharacteristic.objects.filter(
            type_id=self.product.type_id,
            characteristic_id=self.characteristic_id,
        ).exists():
                raise ValidationError(
                {
                    "characteristic": (
                        "Characteristic is not allowed for "
                        "the Product's Type."
                    )
                }
            )

        validate_characteristic_value(self)

    def __str__(self):
        return f"{self.product} — {self.characteristic}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField()
    is_primary = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_product_image"
        ordering = ("product", "id")

    def __str__(self):
        return f"{self.product} — image {self.id}"


class ProductDocumentation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="documentation",
    )
    document = models.FileField()
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_product_documentation"
        ordering = ("product", "id")

    def __str__(self):
        return f"{self.product} — {self.name}"


def validate_assembly_dependency(
    assembly_product_id,
    component_product_id,
):
    if assembly_product_id == component_product_id:
        raise ValidationError(
            {
                "component_product": (
                    "Assembly product cannot be its own component."
                )
            }
        )

    visited = set()
    stack = [component_product_id]

    while stack:
        current_product_id = stack.pop()

        if current_product_id in visited:
            continue

        visited.add(current_product_id)

        if current_product_id == assembly_product_id:
            raise ValidationError(
                {
                    "component_product": (
                        "Circular dependency detected between "
                        "assembly products."
                    )
                }
            )

        next_product_ids = AssemblyComponent.objects.filter(
            assembly_product_id=current_product_id,
        ).values_list(
            "component_product_id",
            flat=True,
        )

        stack.extend(next_product_ids)

def validate_assembly_quantity(quantity):
    if quantity is None:
        raise ValidationError(
            {"quantity": "Quantity is required."}
        )

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValidationError(
            {"quantity": "Quantity must be greater than zero."}
        )

    if quantity.as_tuple().exponent < -3:
        raise ValidationError(
            {
                "quantity": (
                    "Quantity must have no more than "
                    "3 decimal places."
                )
            }
        )


class AssemblyComponent(models.Model):
    assembly_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="assembly_components",
    )
    component_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="used_in_assemblies",
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    class Meta:
        db_table = "catalog_assembly_component"
        constraints = (
            models.UniqueConstraint(
                fields=("assembly_product", "component_product"),
                name="uq_assembly_component",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="ck_assembly_component_quantity_positive",
            ),
        )

    def clean(self):
        validate_assembly_quantity(self.quantity)

        validate_assembly_dependency(
            self.assembly_product_id,
            self.component_product_id,
        )

    def __str__(self):
        return (
            f"{self.assembly_product} — "
            f"{self.component_product} × {self.quantity}"
        )
