"""Build localized product descriptions from linked classification records."""

import textwrap


class ProductDescriptionService:
    LANGUAGES = ("en", "ru", "uk")
    INDENT = "    "
    CLASSIFIERS = (
        ("category", "cat_description"),
        ("group", "grp_description"),
        ("type", "typ_description"),
        ("type_model", "mdl_description"),
        ("execution", "exc_description"),
        ("protection_degree", "ptd_description"),
        ("color", "clr_description"),
        ("supply_variant", "sup_description"),
        ("brand", "brd_description"),
        ("series", "ser_description"),
    )

    @classmethod
    def build(cls, product, language):
        descriptions = []
        for relation_name, description_field in cls.CLASSIFIERS:
            if not getattr(product, f"{relation_name}_id", None):
                continue

            classifier = getattr(product, relation_name)
            description = (
                getattr(classifier, f"{description_field}_{language}", None)
                or getattr(classifier, description_field, "")
                or ""
            )
            description = str(description).strip()
            if description:
                descriptions.append(textwrap.indent(description, cls.INDENT))

        return "\n".join(descriptions)

    @classmethod
    def populate(cls, product):
        for language in cls.LANGUAGES:
            setattr(
                product,
                f"prd_description_{language}",
                cls.build(product, language),
            )
