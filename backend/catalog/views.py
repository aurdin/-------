from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response

from catalog.models import (
    Category,
    Group,
    Brand,
    Series,
    Type,
    Model,
    Execution,
    Color,
    Product,
    Characteristic,
    ProductCharacteristic,
)

from catalog.serializers import (
    ProductSerializer,
    CatalogFilterItemSerializer,
    CatalogFilterCharacteristicSerializer,
)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = (
            Product.objects.filter(status=True)
            .select_related(
                "category",
                "group",
                "brand",
                "series",
                "type",
                "model",
                "execution",
                "color",
            )
            .prefetch_related(
                "characteristics__characteristic",
                "characteristics__value_reference",
                "images",
            )
            .distinct()
        )

        params = self.request.query_params
        search = params.get("search")

        # Search has priority over all filters.
        if search:
            return queryset.filter(
                Q(article__icontains=search)
                | Q(type__name__icontains=search)
                | Q(model__name__icontains=search)
                | Q(execution__name__icontains=search)
                | Q(brand__name__icontains=search)
                | Q(series__name__icontains=search)
                | Q(category__name__icontains=search)
                | Q(group__name__icontains=search)
                | Q(color__name__icontains=search)
                | Q(protection_degree__icontains=search)
                | Q(barcode__icontains=search)
                | Q(packaging__icontains=search)
                | Q(manufacturer_name__icontains=search)
                | Q(manufacturer_description__icontains=search)
                | Q(characteristics__characteristic__name__icontains=search)
                | Q(characteristics__value_text__icontains=search)
                | Q(characteristics__value_reference__value__icontains=search)
            )

        filters = {
            "category": "category_id",
            "group": "group_id",
            "brand": "brand_id",
            "series": "series_id",
            "type": "type_id",
            "model": "model_id",
            "execution": "execution_id",
            "color": "color_id",
            "protection_degree": "protection_degree",
            "article": "article",
        }

        for parameter, field in filters.items():
            value = params.get(parameter)

            if value:
                queryset = queryset.filter(**{field: value})

        characteristics = params.getlist("characteristic")

        for item in characteristics:
            try:
                characteristic_id, value = item.split(":", 1)
                characteristic_id = int(characteristic_id)
            except (TypeError, ValueError):
                queryset = queryset.none()
                continue

            characteristic = Characteristic.objects.filter(
                id=characteristic_id,
            ).first()

            if characteristic is None:
                queryset = queryset.none()
                continue

            characteristic_filter = {
                "characteristics__characteristic_id": characteristic_id,
                "characteristics__status": True,
            }

            if characteristic.value_type == Characteristic.VALUE_TYPE_NUMBER:
                characteristic_filter["characteristics__value_number"] = value

            elif characteristic.value_type == Characteristic.VALUE_TYPE_TEXT:
                characteristic_filter["characteristics__value_text"] = value

            elif characteristic.value_type == Characteristic.VALUE_TYPE_BOOLEAN:
                if value.lower() not in ("true", "false"):
                    queryset = queryset.none()
                    continue

                characteristic_filter["characteristics__value_boolean"] = (
                    value.lower() == "true"
                )

            elif characteristic.value_type == Characteristic.VALUE_TYPE_REFERENCE:
                characteristic_filter["characteristics__value_reference__value"] = value

            else:
                queryset = queryset.none()
                continue

            queryset = queryset.filter(**characteristic_filter)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        if not serializer.data:
            return Response(
                {
                    "results": [],
                    "message": "Товары не найдены.",
                }
            )

        return Response(
            {
                "results": serializer.data,
                "message": None,
            }
        )


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Product.objects.filter(status=True)
            .select_related(
                "category",
                "group",
                "brand",
                "series",
                "type",
                "model",
                "execution",
                "color",
            )
            .prefetch_related(
                "characteristics__characteristic",
                "characteristics__value_reference",
                "images",
            )
        )


class CatalogFiltersView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        active_products = Product.objects.filter(status=True)

        categories = (
            Category.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        groups = (
            Group.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        brands = (
            Brand.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        series = (
            Series.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        types = (
            Type.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        models = (
            Model.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        executions = (
            Execution.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )

        colors = (
            Color.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("name")
        )
        # -----------------------------------

        characteristics = (
            Characteristic.objects.filter(
                product_characteristics__product__in=active_products,
                product_characteristics__status=True,
            )
            .distinct()
            .order_by("name")
        )

        characteristic_data = []

        for characteristic in characteristics:
            product_characteristics = ProductCharacteristic.objects.filter(
                product__in=active_products,
                characteristic=characteristic,
                status=True,
            ).select_related("value_reference")

            values = set()

            for product_characteristic in product_characteristics:
                if characteristic.value_type == Characteristic.VALUE_TYPE_NUMBER:
                    value = product_characteristic.value_number
                    if value is not None:
                        values.add(format(value, "f").rstrip("0").rstrip(".") or "0")

                elif characteristic.value_type == Characteristic.VALUE_TYPE_TEXT:
                    value = product_characteristic.value_text
                    if value is not None and value != "":
                        values.add(value)

                elif characteristic.value_type == Characteristic.VALUE_TYPE_BOOLEAN:
                    value = product_characteristic.value_boolean
                    if value is not None:
                        values.add(str(value).lower())

                elif characteristic.value_type == Characteristic.VALUE_TYPE_REFERENCE:
                    value_reference = product_characteristic.value_reference
                    if value_reference is not None:
                        values.add(value_reference.value)

            characteristic_data.append(
                {
                    "id": characteristic.id,
                    "name": characteristic.name,
                    "value_type": characteristic.value_type,
                    "unit": characteristic.unit,
                    "values": [{"value": value} for value in sorted(values)],
                }
            )
        # -------------------------------

        return Response(
            {
                "categories": CatalogFilterItemSerializer(
                    categories,
                    many=True,
                ).data,
                "groups": CatalogFilterItemSerializer(
                    groups,
                    many=True,
                ).data,
                "brands": CatalogFilterItemSerializer(
                    brands,
                    many=True,
                ).data,
                "series": CatalogFilterItemSerializer(
                    series,
                    many=True,
                ).data,
                "types": CatalogFilterItemSerializer(
                    types,
                    many=True,
                ).data,
                "models": CatalogFilterItemSerializer(
                    models,
                    many=True,
                ).data,
                "executions": CatalogFilterItemSerializer(
                    executions,
                    many=True,
                ).data,
                "colors": CatalogFilterItemSerializer(
                    colors,
                    many=True,
                ).data,
                "characteristics": CatalogFilterCharacteristicSerializer(
                    characteristic_data, many=True
                ).data,
            }
        )
