from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response

from apps.catalog.models import (
    Product,
    ProductCharacteristic,
)
from apps.directory.common.models import (
    Category,
    Group,
    Brand,
    Series,
    Type,
    TypeModel,
    Execution,
    Color,
)
from apps.directory.characteristics.models import Characteristic

from apps.catalog.serializers import (
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
                "type_model",
                "execution",
                "color",
                "protection_degree",
                "supply_variant",
            )
            .prefetch_related(
                "characteristics__characteristic",
                "characteristics__value_reference",
            )
            .distinct()
        )

        params = self.request.query_params
        search = params.get("search")

        # Search has priority over all filters.
        if search:
            return queryset.filter(
                Q(prd_article__icontains=search)
                | Q(prd_code__icontains=search)
                | Q(prd_name__icontains=search)
                | Q(type__typ_name__icontains=search)
                | Q(type_model__mdl_name__icontains=search)
                | Q(execution__exc_name__icontains=search)
                | Q(brand__brd_name__icontains=search)
                | Q(series__ser_name__icontains=search)
                | Q(category__cat_name__icontains=search)
                | Q(group__grp_name__icontains=search)
                | Q(color__clr_name__icontains=search)
                | Q(protection_degree__ptd_name__icontains=search)
                | Q(barcode__icontains=search)
                | Q(packaging__icontains=search)
                | Q(prd_description__icontains=search)
                | Q(prd_notes__icontains=search)
                | Q(characteristics__characteristic__chr_name__icontains=search)
                | Q(characteristics__value_text__icontains=search)
                | Q(characteristics__value_reference__cv_value__icontains=search)
            )

        filters = {
            "category": "category_id",
            "group": "group_id",
            "brand": "brand_id",
            "series": "series_id",
            "type": "type_id",
            "execution": "execution_id",
            "color": "color_id",
            "protection_degree": "protection_degree_id",
            "article": "prd_article",
            "type_model": "type_model_id",
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
            value_type = ProductCharacteristic.objects.filter(
                product__in=queryset,
                characteristic_id=characteristic_id,
                status=True,
            ).values_list("value_type", flat=True).first()

            if value_type == "number":
                characteristic_filter["characteristics__value_number"] = value

            elif value_type == "text":
                characteristic_filter["characteristics__value_text"] = value

            elif value_type == "boolean":
                if value.lower() not in ("true", "false"):
                    queryset = queryset.none()
                    continue

                characteristic_filter["characteristics__value_boolean"] = (
                    value.lower() == "true"
                )

            elif value_type == "reference":
                characteristic_filter["characteristics__value_reference__cv_value"] = value

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
                "type_model",
                "execution",
                "color",
                "protection_degree",
                "supply_variant",
            )
            .prefetch_related(
                "characteristics__characteristic",
                "characteristics__value_reference",
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
            .order_by("cat_name")
        )

        groups = (
            Group.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("grp_name")
        )

        brands = (
            Brand.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("brd_name")
        )

        series = (
            Series.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("ser_name")
        )

        types = (
            Type.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("typ_name")
        )

        models = (
            TypeModel.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("mdl_name")
        )

        executions = (
            Execution.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("exc_name")
        )

        colors = (
            Color.objects.filter(
                products__in=active_products,
            )
            .distinct()
            .order_by("clr_name")
        )
        # -----------------------------------

        characteristics = (
            Characteristic.objects.filter(
                product_characteristics__product__in=active_products,
                product_characteristics__status=True,
            )
            .distinct()
            .order_by("chr_name")
        )

        characteristic_data = []

        for characteristic in characteristics:
            product_characteristics = ProductCharacteristic.objects.filter(
                product__in=active_products,
                characteristic=characteristic,
                status=True,
            ).select_related("value_reference")

            values = set()
            value_type = product_characteristics.values_list("value_type", flat=True).first()

            for product_characteristic in product_characteristics:
                if value_type == "number":
                    value = product_characteristic.value_number
                    if value is not None:
                        values.add(format(value, "f").rstrip("0").rstrip(".") or "0")

                elif value_type == "text":
                    value = product_characteristic.value_text
                    if value is not None and value != "":
                        values.add(value)

                elif value_type == "boolean":
                    value = product_characteristic.value_boolean
                    if value is not None:
                        values.add(str(value).lower())

                elif value_type == "reference":
                    value_reference = product_characteristic.value_reference
                    if value_reference is not None:
                        values.add(value_reference.cv_value)

            characteristic_data.append(
                {
                    "id": characteristic.id,
                    "name": characteristic.chr_name,
                    "value_type": value_type or "text",
                    "unit": characteristic.chr_unit.unt_name if characteristic.chr_unit_id else None,
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

