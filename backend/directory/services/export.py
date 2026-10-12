from io import BytesIO

from django.db import models
from openpyxl import Workbook
from datetime import datetime


class DirectoryExportService:
    """Универсальный экспорт справочников в Excel."""

    @staticmethod
    def export(queryset):
        model = queryset.model

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = model._meta.model_name[:31]

        fields = DirectoryExportService._get_export_fields(model)

        worksheet.append(
            [field["header"] for field in fields]
        )

        for obj in queryset.order_by("id"):
            worksheet.append(
                [
                    DirectoryExportService._get_value(obj, field)
                    for field in fields
                ]
            )

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        return output

    @staticmethod
    def _get_export_fields(model):
        """Определяет все поля модели, пригодные для экспорта."""

        fields = []

        for field in model._meta.get_fields():
            if not field.concrete:
                continue

            if isinstance(field, models.ForeignKey):
                fields.append(
                    {
                        "header": field.name,
                        "field": field.name,
                        "type": "foreign_key",
                    }
                )
                fields.append(
                    {
                        "header": f"{field.name}_value",
                        "field": field.name,
                        "type": "foreign_key_value",
                    }
                )
                continue

            fields.append(
                {
                    "header": field.name,
                    "field": field.name,
                    "type": "field",
                }
            )

        return fields

    @staticmethod
    def _get_value(obj, field):
        field_name = field["field"]
        field_type = field["type"]

        if field_type == "foreign_key":
            return getattr(obj, f"{field_name}_id", None)

        if field_type == "foreign_key_value":
            related_object = getattr(obj, field_name, None)

            if related_object is None:
                return None

            return DirectoryExportService._get_related_value(
                related_object
            )

        value = getattr(obj, field_name, None)

        if isinstance(value, datetime) and value.tzinfo is not None:
            return value.replace(tzinfo=None)

        return value
        
    @staticmethod
    def _get_related_value(obj):
        """Возвращает информативное значение связанного объекта."""

        for field in obj._meta.get_fields():
            if not field.concrete:
                continue

            if field.name == "id":
                continue

            if field.name.endswith("_code"):
                return getattr(obj, field.name)

        return str(obj)