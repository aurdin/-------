from rest_framework import serializers

from prices.models import Currency, Discount, Price


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = (
            "id",
            "code",
            "name",
            "symbol",
            "is_active",
        )


class PriceSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(read_only=True)

    class Meta:
        model = Price
        fields = (
            "id",
            "product",
            "currency",
            "amount",
            "valid_from",
            "valid_to",
        )


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = (
            "id",
            "product",
            "type",
            "value",
            "valid_from",
            "valid_to",
            "is_active",
        )
