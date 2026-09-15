from rest_framework import serializers

from catalog.models import (
    Product,
    ProductCharacteristic,
    ProductImage,
)
from catalog.services.product_name import ProductNameService


class ProductCharacteristicSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="characteristic.name",
        read_only=True,
    )

    value_type = serializers.CharField(
        source="characteristic.value_type",
        read_only=True,
    )

    unit = serializers.CharField(
        source="characteristic.unit",
        read_only=True,
    )

    value = serializers.SerializerMethodField()

    class Meta:
        model = ProductCharacteristic
        fields = (
            "id",
            "name",
            "value_type",
            "value",
            "unit",
            "status",
        )

    def get_value(self, obj):
        characteristic = obj.characteristic

        if characteristic.value_type == "text":
            return obj.value_text

        if characteristic.value_type == "number":
            return obj.value_number

        if characteristic.value_type == "boolean":
            return obj.value_boolean

        if characteristic.value_type == "reference":
            if obj.value_reference_id:
                return obj.value_reference.value
            return None

        return None


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "image",
            "status",
        )


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    category = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    execution = serializers.SerializerMethodField()

    color = serializers.SerializerMethodField()

    characteristics = ProductCharacteristicSerializer(
        many=True,
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "article",
            "name",
            "category",
            "group",
            "brand",
            "series",
            "type",
            "model",
            "execution",
            "protection_degree",
            "color",
            "characteristics",
            "packaging",
            "sales_unit",
            "barcode",
            "images",
            "status",
        )

    def get_name(self, obj):
        return ProductNameService.build(obj)

    @staticmethod
    def _reference(obj):
        if obj is None:
            return None

        return {
            "id": obj.id,
            "name": obj.name,
        }

    def get_category(self, obj):
        return self._reference(obj.category)

    def get_group(self, obj):
        return self._reference(obj.group)

    def get_brand(self, obj):
        return self._reference(obj.brand)

    def get_series(self, obj):
        return self._reference(obj.series)

    def get_type(self, obj):
        return self._reference(obj.type)

    def get_model(self, obj):
        return self._reference(obj.model)

    def get_execution(self, obj):
        return self._reference(obj.execution)

    def get_color(self, obj):
        return self._reference(obj.color)


class CatalogFilterItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class CatalogFilterCharacteristicValueSerializer(serializers.Serializer):
    value = serializers.CharField()


class CatalogFilterCharacteristicSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    value_type = serializers.CharField()
    unit = serializers.CharField(allow_null=True)
    values = CatalogFilterCharacteristicValueSerializer(many=True)
