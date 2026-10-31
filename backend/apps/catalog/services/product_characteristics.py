"""Build localized product characteristic summaries."""

from apps.catalog.services.naming import ProductNameService


class ProductCharacteristicsService:
    LANGUAGES = ProductNameService.LANGUAGES

    @classmethod
    def build(cls, product, language):
        if not product.pk:
            return ""

        lines = []
        characteristics = product.characteristics.filter(status=True).select_related(
            "characteristic__chr_unit", "unit", "value_reference"
        ).order_by("id")

        for item in characteristics:
            name = ProductNameService.translated(
                item.characteristic, "chr_name", language
            )
            value = ProductNameService.characteristic_values_for_item(item, language)
            if not value:
                continue

            description = ProductNameService.translated(
                item.characteristic, "chr_description", language
            )
            parts = [part for part in (name, value) if part]
            line = ", ".join(parts)
            if description:
                line = f"{line} — {description}" if line else description
            if line:
                lines.append(line)

        return "\n".join(lines)

    @classmethod
    def populate(cls, product):
        for language in cls.LANGUAGES:
            setattr(
                product,
                f"prd_characteristics_{language}",
                cls.build(product, language),
            )
