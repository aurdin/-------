from rest_framework import serializers

from .models import Stock, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = (
            "id",
            "product",
            "warehouse",
            "quantity_available",
            "quantity_reserved",
            "quantity_incoming",
            "quantity_on_order",
            "is_discontinued",
            "status",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "quantity_available",
            "quantity_reserved",
            "quantity_incoming",
            "quantity_on_order",
            "status",
            "updated_at",
        )


class StockOperationSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля.")
        return value


class StockAdjustmentSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Количество не должно быть равно нулю.")
        return value
