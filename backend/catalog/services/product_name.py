from __future__ import annotations


class ProductNameService:
    """
    Формирует отображаемое имя товара на основании его параметров.

    Порядок:
    Type → Model → Execution → Protection degree →
    Product characteristics → Brand → Series → Color
    """

    @staticmethod
    def build(product) -> str:
        parts = []

        # 1. Type
        if product.type_id:
            parts.append(product.type.name)

        # 2. Model
        if product.model_id:
            parts.append(product.model.name)

        # 3. Execution
        if product.execution_id:
            parts.append(product.execution.name)

        # 4. Protection degree
        if product.protection_degree:
            parts.append(product.protection_degree)

        # 5. Product characteristics
        parts.extend(ProductNameService._get_characteristics(product))

        # 6. Brand
        if product.brand_id:
            parts.append(product.brand.name)

        # 7. Series
        if product.series_id:
            parts.append(product.series.name)

        # 8. Color — всегда последним
        if product.color_id and product.color.status:
            parts.append(product.color.name)

        return " ".join(part.strip() for part in parts if part and part.strip())

    @staticmethod
    def _get_characteristics(product) -> list[str]:
        result = []

        characteristics = (
            product.characteristics.filter(status=True)
            .select_related(
                "characteristic",
                "value_reference",
            )
            .order_by("id")
        )

        for item in characteristics:
            characteristic = item.characteristic

            if characteristic.value_type == "text":
                value = item.value_text

            elif characteristic.value_type == "number":
                value = item.value_number

            elif characteristic.value_type == "boolean":
                value = item.value_boolean

            elif characteristic.value_type == "reference":
                value = item.value_reference.value if item.value_reference_id else None

            else:
                value = None

            if value is None:
                continue

            if isinstance(value, bool):
                value = "Да" if value else "Нет"

            elif characteristic.value_type == "number":
                value = format(value, "f").rstrip("0").rstrip(".")

            value = str(value).strip()

            if not value:
                continue

            if characteristic.unit:
                value = f"{value} {characteristic.unit}"

            result.append(value)

        return result
