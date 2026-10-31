"""Keep product descriptions in sync with classification descriptions."""

from django.db.models.signals import post_save
from django.db.models import Q
from django.dispatch import receiver

from apps.catalog.models import Product, ProductCharacteristic
from apps.directory.characteristics.models import Characteristic, CharacteristicValue, Unit
from apps.catalog.services.descriptions import ProductDescriptionService
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


CLASSIFIER_PRODUCT_FIELDS = {
    Category: "category",
    Group: "group",
    Type: "type",
    TypeModel: "type_model",
    Execution: "execution",
    ProtectionDegree: "protection_degree",
    Color: "color",
    SupplyVariant: "supply_variant",
    Brand: "brand",
    Series: "series",
}


@receiver(post_save, sender=Category)
@receiver(post_save, sender=Group)
@receiver(post_save, sender=Type)
@receiver(post_save, sender=TypeModel)
@receiver(post_save, sender=Execution)
@receiver(post_save, sender=ProtectionDegree)
@receiver(post_save, sender=Color)
@receiver(post_save, sender=SupplyVariant)
@receiver(post_save, sender=Brand)
@receiver(post_save, sender=Series)
def refresh_product_descriptions(sender, instance, **kwargs):
    product_field = CLASSIFIER_PRODUCT_FIELDS[sender]
    products = Product.objects.filter(**{f"{product_field}_id": instance.pk})
    update_fields = tuple(
        f"prd_description_{language}"
        for language in ProductDescriptionService.LANGUAGES
    )

    for product in products.iterator():
        ProductDescriptionService.populate(product)
        Product.objects.filter(pk=product.pk).update(
            **{
                field: getattr(product, field)
                for field in update_fields
            }
        )


def refresh_generated_product_characteristics(product_ids):
    update_fields = ProductCharacteristic.product_generated_fields()
    for product in Product.objects.filter(pk__in=product_ids).iterator():
        product.save(update_fields=update_fields)


@receiver(post_save, sender=Characteristic)
def refresh_characteristic_products(sender, instance, **kwargs):
    product_ids = ProductCharacteristic.objects.filter(
        characteristic_id=instance.pk
    ).values_list("product_id", flat=True)
    refresh_generated_product_characteristics(product_ids)


@receiver(post_save, sender=Unit)
def refresh_unit_products(sender, instance, **kwargs):
    product_ids = ProductCharacteristic.objects.filter(
        Q(unit_id=instance.pk) | Q(characteristic__chr_unit_id=instance.pk)
    ).values_list("product_id", flat=True)
    refresh_generated_product_characteristics(product_ids)


@receiver(post_save, sender=CharacteristicValue)
def refresh_characteristic_value_products(sender, instance, **kwargs):
    product_ids = ProductCharacteristic.objects.filter(
        value_reference_id=instance.pk
    ).values_list("product_id", flat=True)
    refresh_generated_product_characteristics(product_ids)
