from rest_framework import serializers

from catalog.models import Product
from cart.models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "article",
        )
        read_only_fields = (
            "id",
            "article",
        )


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(status=True),
        write_only=True,
    )

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "product_id",
            "quantity",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "product",
            "created_at",
            "updated_at",
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = (
            "id",
            "status",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "items",
            "created_at",
            "updated_at",
        )
