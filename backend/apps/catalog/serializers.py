from rest_framework import serializers
from django.utils.translation import get_language

from apps.catalog.models import (
    Product,
    ProductCharacteristic,
)
from apps.catalog.services.naming import ProductNameService


class ProductCharacteristicSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="characteristic.chr_name",
        read_only=True,
    )

    value_type = serializers.CharField(read_only=True)

    unit = serializers.CharField(source="characteristic.chr_unit.unt_name", read_only=True, allow_null=True)

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
        if obj.value_type == "text":
            return obj.value_text

        if obj.value_type == "number":
            return obj.value_number

        if obj.value_type == "boolean":
            return obj.value_boolean

        if obj.value_type == "reference":
            if obj.value_reference_id:
                return obj.value_reference.cv_value
            return None

        return None


class ProductImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    image = serializers.CharField()
    status = serializers.BooleanField()



class ProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    article = serializers.CharField(source="prd_article", read_only=True)

    category = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    execution = serializers.SerializerMethodField()
    protection_degree = serializers.SerializerMethodField()

    color = serializers.SerializerMethodField()

    characteristics = ProductCharacteristicSerializer(
        many=True,
        read_only=True,
    )

    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "prd_code",
            "article",
            "name",
            "prd_description",
            "prd_notes",
            "date_created",
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
        language = (get_language() or "ru").split("-", 1)[0]
        if language not in ProductNameService.LANGUAGES:
            language = "ru"
        return getattr(obj, f"prd_name_{language}", None) or ProductNameService.build(obj, language)

    def get_images(self, obj):
        return [
            {"id": index, "image": getattr(obj, field).url, "status": True}
            for index, field in enumerate(("product_image_1", "product_image_2", "product_image_3"), start=1)
            if getattr(obj, field)
        ]

    @staticmethod
    def _reference(obj):
        if obj is None:
            return None

        return {
            "id": obj.id,
            "name": str(obj),
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
        return self._reference(obj.type_model)

    def get_execution(self, obj):
        return self._reference(obj.execution)

    def get_protection_degree(self, obj):
        return obj.protection_degree.ptd_name if obj.protection_degree_id else None

    def get_color(self, obj):
        return self._reference(obj.color)


class CatalogFilterItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return str(obj)


class CatalogFilterCharacteristicValueSerializer(serializers.Serializer):
    value = serializers.CharField()


class CatalogFilterCharacteristicSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    value_type = serializers.CharField()
    unit = serializers.CharField(allow_null=True)
    values = CatalogFilterCharacteristicValueSerializer(many=True)

