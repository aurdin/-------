"""Product import with code/article matching and bounded row errors."""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Product
from apps.directory.services.import_service import DirectoryImportService


class ProductImportCancelled(Exception):
    """Raised to roll back the complete import after the error limit is exceeded."""


class ProductImportService:
    MAX_ERRORS = 10

    @classmethod
    def import_rows(cls, data):
        errors = []
        created = 0
        updated = 0
        try:
            with transaction.atomic():
                for row in data:
                    row_number = row["row_number"]
                    try:
                        with transaction.atomic():
                            action = cls._import_row(row)
                        if action == "create":
                            created += 1
                        else:
                            updated += 1
                    except Exception as exc:
                        detail = "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
                        errors.append({"row": row_number, "message": detail})
                        if len(errors) > cls.MAX_ERRORS:
                            raise ProductImportCancelled
        except ProductImportCancelled:
            return {"created": 0, "updated": 0, "errors": errors, "cancelled": True}
        return {"created": created, "updated": updated, "errors": errors, "cancelled": False}

    @staticmethod
    def _import_row(row):
        values = row["values"]
        raw_code = values.get("prd_code")
        code = str(raw_code).strip() if raw_code is not None else ""
        raw_article = values.get("prd_article")
        article = str(raw_article).strip() if raw_article is not None else ""

        code_match = Product.objects.filter(prd_code=code).first() if code else None
        article_match = Product.objects.filter(prd_article=article).first() if article else None

        if code and code_match and article_match and code_match.pk != article_match.pk:
            raise ValidationError("prd_code and prd_article identify different products.")
        if code and article_match and not code_match:
            raise ValidationError("The article already belongs to a product with a different code.")
        if not code and article_match:
            raise ValidationError("The article already exists; a row without prd_code is skipped.")

        instance = code_match
        action = "update" if instance else "create"
        prepared = {
            "row_number": row["row_number"],
            "code": code or None,
            "instance": instance,
            "action": action,
            "values": values,
        }
        instance = DirectoryImportService.prepare_instance(Product, prepared)
        instance.full_clean()
        instance.save()
        return action
