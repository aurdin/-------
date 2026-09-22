from rest_framework import serializers

from orders.models import Order, OrderItem


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
