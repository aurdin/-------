from django.core.exceptions import ValidationError
from django.db import  models, transaction
from openpyxl import load_workbook


class DirectoryImportService:
    """Универсальный импорт справочников из Excel."""

    @staticmethod
    def get_code_field(model):
        """Возвращает поле бизнес-кода модели."""

        code_fields = [
            field
            for field in model._meta.fields
            if field.name.endswith("_code")
        ]

        if len(code_fields) != 1:
            raise ValidationError(
                f"Model {model.__name__} must have exactly one code field."
            )

        return code_fields[0]

    @staticmethod
    def read_workbook(file):
        """Читает Excel-файл и возвращает строки с заголовками."""

        workbook = load_workbook(
            file,
            data_only=True,
        )

        worksheet = workbook.active

        rows = list(worksheet.iter_rows(values_only=True))

        if not rows:
            raise ValidationError("Excel file is empty.")

        headers = [
            str(value).strip() if value is not None else ""
            for value in rows[0]
        ]

        if not any(headers):
            raise ValidationError("Excel header row is empty.")

        data = []

        for row_number, row in enumerate(rows[1:], start=2):
            if not any(value is not None for value in row):
                continue

            data.append(
                {
                    "row_number": row_number,
                    "values": dict(zip(headers, row)),
                }
            )

        return headers, data

    @staticmethod
    def validate_headers(model, headers):
        """Проверяет наличие необходимых колонок."""

        code_field = DirectoryImportService.get_code_field(model)

        if code_field.name not in headers:
            raise ValidationError(
                f"Required column '{code_field.name}' is missing."
            )

        return True

    @staticmethod
    def prepare_rows(model, data):
        """Определяет, какие записи будут созданы или обновлены."""

        code_field = DirectoryImportService.get_code_field(model)

        prepared = []

        for row in data:
            values = row["values"]
            raw_code = values.get(code_field.name)

            code = (
                str(raw_code).strip()
                if raw_code is not None
                else ""
            )

            instance = None

            if code:
                instance = model.objects.filter(
                    **{code_field.name: code}
                ).first()

            prepared.append(
                {
                    "row_number": row["row_number"],
                    "code": code or None,
                    "instance": instance,
                    "action": "update" if instance else "create",
                    "values": values,
                }
            )

        return prepared

    @staticmethod
    def build_instance(model, prepared_row):
        """Создаёт или получает объект без сохранения в БД."""

        instance = prepared_row["instance"]

        if instance is not None:
            return instance

        code = prepared_row["code"]

        if code:
            return model(
                **{
                    DirectoryImportService.get_code_field(model).name: code
                }
            )

        return model() 

    @staticmethod
    def prepare_instance(model, prepared_row):
        """Готовит объект к сохранению без записи в БД."""

        instance = DirectoryImportService.build_instance(
            model,
            prepared_row,
        )

        DirectoryImportService.apply_values(
            model,
            instance,
            prepared_row["values"],
        )

        return instance 

    @staticmethod
    def import_rows(model, prepared_rows):
        """Сохраняет подготовленные строки в одной транзакции."""

        results = []

        with transaction.atomic():
            for prepared_row in prepared_rows:
                instance = DirectoryImportService.prepare_instance(
                    model,
                    prepared_row,
                )

                instance.full_clean()
                instance.save()

                results.append(
                    {
                        "row_number": prepared_row["row_number"],
                        "code": instance.pk and (
                            getattr(
                                instance,
                                DirectoryImportService.get_code_field(
                                    model
                                ).name,
                            )
                        ),
                        "action": prepared_row["action"],
                        "instance": instance,
                    }
                )

        return results          

    @staticmethod
    def get_import_fields(model):
        """Возвращает поля модели, которые можно импортировать."""

        code_field = DirectoryImportService.get_code_field(model)

        excluded_fields = {
            "id",
            code_field.name,
            "date_created",
            "date_updated",
        }

        return [
            field
            for field in model._meta.fields
            if field.name not in excluded_fields
        ]

    @staticmethod
    def resolve_foreign_key(field, values):
        """Возвращает объект для ForeignKey из данных Excel."""

        field_name = field.name
        value_field = f"{field_name}_value"

        related_model = field.remote_field.model

        related_code_fields = [
            related_field
            for related_field in related_model._meta.fields
            if related_field.name.endswith("_code")
        ]

        if len(related_code_fields) != 1:
            raise ValidationError(
                f"Related model {related_model.__name__} "
                f"must have exactly one code field."
            )

        code_field = related_code_fields[0]

        related_code = values.get(value_field)

        if related_code is not None and str(related_code).strip():
            related_code = str(related_code).strip()

            instance = related_model.objects.filter(
                **{code_field.name: related_code}
            ).first()

            if instance is None:
                raise ValidationError(
                    f"Related object {related_model.__name__} "
                    f"with code '{related_code}' was not found."
                )

            return instance

        related_id = values.get(field_name)

        if related_id is None or str(related_id).strip() == "":
            if field.null:
                return None

            raise ValidationError(
                f"Required relation '{field_name}' is empty."
            )

        instance = related_model.objects.filter(
            pk=related_id
        ).first()

        if instance is None:
            raise ValidationError(
                f"Related object {related_model.__name__} "
                f"with id '{related_id}' was not found."
            )

        return instance    

    @staticmethod
    def apply_values(model, instance, values):
        """Применяет импортируемые значения к объекту без сохранения."""

        import_fields = DirectoryImportService.get_import_fields(model)

        for field in import_fields:
            if isinstance(field, models.ForeignKey):
                value_field = f"{field.name}_value"

                if (
                    field.name not in values
                    and value_field not in values
                ):
                    continue

                setattr(
                    instance,
                    field.name,
                    DirectoryImportService.resolve_foreign_key(
                        field,
                        values,
                    ),
                )
                continue

            if field.name not in values:
                continue

            value = values[field.name]

            if value is None:
                continue

            if isinstance(value, str) and not value.strip():
                continue

            setattr(
                instance,
                field.name,
                value,
            )

        return instance