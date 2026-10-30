"""Build localized product names from the rule configured for each type."""

from decimal import Decimal

class ProductNameService:
    LANGUAGES = ("en", "ru", "uk")
    NO_NAME = "Без названия"

    @classmethod
    def build(cls, product, language="ru"):
        rule = getattr(product.type, "product_name_rule", None) if product.type_id else None
        if rule is None:
            return cls.NO_NAME

        parts = []
        configured_components = list(rule.components.order_by("position"))
        if not configured_components:
            return cls.NO_NAME
        for item in configured_components:
            value = cls.component_value(product, item.component, language)
            if value:
                parts.append(value.strip())
        return " ".join(part for part in parts if part)

    @classmethod
    def populate(cls, product):
        for language in cls.LANGUAGES:
            setattr(product, f"prd_name_{language}", cls.build(product, language))

    @staticmethod
    def translated(obj, field, language):
        if obj is None:
            return ""
        return (getattr(obj, f"{field}_{language}", None) or getattr(obj, field, "") or "").strip()

    @classmethod
    def component_value(cls, product, component, language):
        from apps.catalog.models import ProductNameRuleComponent as Component

        fields = {
            Component.COMPONENT_TYPE: ("type", "typ_name"),
            Component.COMPONENT_MODEL: ("type_model", "mdl_name"),
            Component.COMPONENT_EXECUTION: ("execution", "exc_name"),
            Component.COMPONENT_PROTECTION: ("protection_degree", "ptd_name"),
            Component.COMPONENT_COLOR: ("color", "clr_name"),
            Component.COMPONENT_SUPPLY: ("supply_variant", "sup_name"),
        }
        if component == Component.COMPONENT_CHARACTERISTICS:
            return " ".join(cls.characteristic_values(product, language))
        relation = fields.get(component)
        if relation is None:
            return ""
        relation_name, field_name = relation
        if not getattr(product, f"{relation_name}_id", None):
            return ""
        obj = getattr(product, relation_name)
        if relation_name == "color" and not obj.clr_status:
            return ""
        return cls.translated(obj, field_name, language)

    @classmethod
    def characteristic_values(cls, product, language):
        values = []
        rows = product.characteristics.filter(status=True).select_related(
            "characteristic__chr_unit", "value_reference"
        ).order_by("id")
        for item in rows:
            if item.value_type == "text":
                value = item.value_text
            elif item.value_type == "number" and item.value_number is not None:
                value = format(Decimal(item.value_number), "f").rstrip("0").rstrip(".") or "0"
            elif item.value_type == "boolean" and item.value_boolean is not None:
                value = {
                    "en": "Yes" if item.value_boolean else "No",
                    "ru": "Да" if item.value_boolean else "Нет",
                    "uk": "Так" if item.value_boolean else "Ні",
                }[language]
            elif item.value_type == "reference" and item.value_reference_id:
                value = cls.translated(item.value_reference, "cv_value", language)
            else:
                value = ""
            value = str(value).strip() if value is not None else ""
            if not value:
                continue
            unit = cls.translated(item.characteristic.chr_unit, "unt_name", language)
            values.append(f"{value} {unit}".strip() if unit else value)
        return values
