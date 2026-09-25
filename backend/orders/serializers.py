from rest_framework import serializers

from orders.models import Order, OrderItem, OrderStatus

class CheckoutSerializer(serializers.Serializer):
    currency = serializers.CharField(required=True)

    customer_name = serializers.CharField(required=True)
    customer_phone = serializers.CharField(required=True)

    delivery_first_name = serializers.CharField(required=True)
    delivery_last_name = serializers.CharField(required=True)
    delivery_middle_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    delivery_phone = serializers.CharField(required=False, allow_blank=True)
    delivery_country = serializers.CharField(required=True)
    delivery_region = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    delivery_city = serializers.CharField(required=True)
    delivery_postal_code = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    delivery_address_line = serializers.CharField(required=True)
    delivery_apartment = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "article",
            "product_name",
            "quantity",
            "unit_price",
            "discount",
            "total",
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "status",
            "currency",
            "customer_name",
            "customer_phone",
            "delivery_first_name",
            "delivery_last_name",
            "delivery_middle_name",
            "delivery_phone",
            "delivery_country",
            "delivery_region",
            "delivery_city",
            "delivery_postal_code",
            "delivery_address_line",
            "delivery_apartment",
            "subtotal",
            "product_discount_total",
            "order_discount",
            "promotion_discount",
            "total",
            "created_at",
            "updated_at",
            "items",
        )
        read_only_fields = fields

class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=OrderStatus.choices,
        required=True,
    )