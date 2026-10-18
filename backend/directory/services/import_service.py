from django.core.exceptions import ValidationError
from django.db import models, transaction
from openpyxl import load_workbook  # type: ignore

from apps.catalog.services.codes import generate_code


class DirectoryImportService:
    """Универсальный импорт справочников и связей из Excel."""

    @staticmethod
    def get_code_field(model):
        """Возвращает единственное поле бизнес-кода модели."""

        code_fields = [
            field for field in model._meta.fields if field.name.endswith("_code")
        ]

        if len(code_fields) != 1:
            raise ValidationError(
                f"Model {model.__name__} must have exactly one code field."
            )

        return code_fields[0]

    @staticmethod
    def get_composite_key_fields(model):
        """
        Возвращает два ForeignKey для модели связи без бизнес-кода.

        Обычные справочники обрабатываются по бизнес-коду.
        Модель без бизнес-кода считается моделью связи, если у неё
        ровно два поля ForeignKey.
        """

        code_fields = [
            field for field in model._meta.fields if field.name.endswith("_code")
        ]

        if code_fields:
            return None

        foreign_key_fields = [
            field
            for field in model._meta.fields
            if isinstance(field, models.ForeignKey)
        ]

        if len(foreign_key_fields) != 2:
            raise ValidationError(
                f"Model {model.__name__} has no business-code field "
                "and must have exactly two ForeignKey fields."
            )

        return foreign_key_fields

    @staticmethod
    def is_composite_key_model(model):
        """Определяет, является ли модель связью с составным ключом."""

        return DirectoryImportService.get_composite_key_fields(model) is not None

    @staticmethod
    def read_workbook(file):
        """Читает Excel-файл и возвращает заголовки и строки данных."""

        workbook = load_workbook(
            file,
            data_only=True,
        )

        worksheet = workbook.active
        rows = list(worksheet.iter_rows(values_only=True))

        if not rows:
            raise ValidationError("Excel file is empty.")

        headers = [str(value).strip() if value is not None else "" for value in rows[0]]

        if not any(headers):
            raise ValidationError("Excel header row is empty.")

        if len(headers) != len(set(headers)):
            raise ValidationError("Excel file contains duplicate column headers.")

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
        """Проверяет обязательные колонки Excel."""

        composite_fields = DirectoryImportService.get_composite_key_fields(model)

        if composite_fields is None:
            code_field = DirectoryImportService.get_code_field(model)

            if code_field.name not in headers:
                raise ValidationError(
                    f"Required column '{code_field.name}' is missing."
                )

            return True

        for field in composite_fields:
            value_field = f"{field.name}_value"

            if field.name not in headers and value_field not in headers:
                raise ValidationError(
                    f"Required relation column '{field.name}' "
                    f"or '{value_field}' is missing."
                )

        return True

    @staticmethod
    def prepare_rows(model, data):
        """Находит существующие записи и подготавливает строки импорта."""

        composite_fields = DirectoryImportService.get_composite_key_fields(model)

        if composite_fields is None:
            return DirectoryImportService.prepare_code_rows(model, data)

        prepared = []
        seen_pairs = {}

        for row in data:
            row_number = row["row_number"]
            values = row["values"]

            try:
                resolved_relations = {}

                for field in composite_fields:
                    resolved_relations[field.name] = (
                        DirectoryImportService.resolve_foreign_key(
                            field,
                            values,
                        )
                    )

                pair = tuple(
                    resolved_relations[field.name].pk
                    if resolved_relations[field.name] is not None
                    else None
                    for field in composite_fields
                )

                if pair in seen_pairs:
                    first_row_number = seen_pairs[pair]

                    raise ValidationError(
                        f"Duplicate relationship in Excel rows "
                        f"{first_row_number} and {row_number}."
                    )

                seen_pairs[pair] = row_number

                lookup = {
                    field.name: resolved_relations[field.name]
                    for field in composite_fields
                }

                instance = model.objects.filter(**lookup).first()

                prepared.append(
                    {
                        "row_number": row_number,
                        "code": None,
                        "instance": instance,
                        "action": "update" if instance else "create",
                        "values": values,
                        "resolved_relations": resolved_relations,
                    }
                )

            except ValidationError as exc:
                raise ValidationError(f"Excel row {row_number}: {exc}") from exc

        return prepared

    @staticmethod
    def prepare_code_rows(model, data):
        """Подготавливает обычные справочники по бизнес-коду."""

        code_field = DirectoryImportService.get_code_field(model)
        prepared = []

        for row in data:
            values = row["values"]
            raw_code = values.get(code_field.name)

            code = str(raw_code).strip() if raw_code is not None else ""

            instance = None

            if code:
                instance = model.objects.filter(**{code_field.name: code}).first()

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
        """Создаёт новый объект или возвращает существующий."""

        instance = prepared_row["instance"]

        if instance is not None:
            return instance

        composite_fields = DirectoryImportService.get_composite_key_fields(model)

        if composite_fields is not None:
            return model(**prepared_row["resolved_relations"])

        code_field = DirectoryImportService.get_code_field(model)
        code = prepared_row["code"]

        if code:
            return model(**{code_field.name: code})

        instance = model()
        prefix = code_field.name.rsplit("_", 1)[0]

        setattr(
            instance,
            code_field.name,
            generate_code(model, code_field.name, prefix),
        )

        return instance

    @staticmethod
    def prepare_instance(model, prepared_row):
        """Применяет значения к объекту без предварительного сохранения."""

        instance = DirectoryImportService.build_instance(
            model,
            prepared_row,
        )

        DirectoryImportService.apply_values(
            model,
            instance,
            prepared_row["values"],
        )

        # Для моделей связей используем уже разрешённую пару FK.
        # Это исключает повторное сопоставление по значениям Excel.
        resolved_relations = prepared_row.get("resolved_relations", {})

        for field_name, related_instance in resolved_relations.items():
            setattr(instance, field_name, related_instance)

        return instance

    @staticmethod
    def import_rows(model, prepared_rows):
        """Сохраняет все строки в одной транзакции."""

        results = []

        with transaction.atomic():
            for prepared_row in prepared_rows:
                row_number = prepared_row["row_number"]

                try:
                    instance = DirectoryImportService.prepare_instance(
                        model,
                        prepared_row,
                    )

                    instance.full_clean()
                    instance.save()

                    composite_fields = DirectoryImportService.get_composite_key_fields(
                        model
                    )

                    if composite_fields is None:
                        code_field = DirectoryImportService.get_code_field(model)
                        code = getattr(instance, code_field.name)
                    else:
                        code = None

                    results.append(
                        {
                            "row_number": row_number,
                            "code": code,
                            "action": prepared_row["action"],
                            "instance": instance,
                        }
                    )

                except ValidationError as exc:
                    raise ValidationError(f"Excel row {row_number}: {exc}") from exc

                except Exception as exc:
                    raise ValidationError(f"Excel row {row_number}: {exc}") from exc

        return results

    @staticmethod
    def get_import_fields(model):
        """Возвращает поля модели, доступные для импорта."""

        excluded_fields = {
            "id",
            "date_created",
            "date_updated",
        }

        code_fields = [
            field for field in model._meta.fields if field.name.endswith("_code")
        ]

        if len(code_fields) == 1:
            excluded_fields.add(code_fields[0].name)

        return [
            field for field in model._meta.fields if field.name not in excluded_fields
        ]

    @staticmethod
    def resolve_foreign_key(field, values):
        """Разрешает ForeignKey по бизнес-коду или числовому ID."""

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
                "must have exactly one code field."
            )

        code_field = related_code_fields[0]
        related_code = values.get(value_field)

        # При наличии кода используем его в первую очередь.
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

        # Если код отсутствует или пуст, используем ID из Excel.
        related_id = values.get(field_name)

        if related_id is None or str(related_id).strip() == "":
            if field.null:
                return None

            raise ValidationError(f"Required relation '{field_name}' is empty.")

        # Excel может возвращать числовые ячейки как 1.0.
        if isinstance(related_id, float) and related_id.is_integer():
            related_id = int(related_id)

        if isinstance(related_id, str):
            related_id = related_id.strip()

            if related_id.endswith(".0"):
                numeric_part = related_id[:-2]
                if numeric_part.isdigit():
                    related_id = int(numeric_part)

        instance = related_model.objects.filter(pk=related_id).first()

        if instance is None:
            raise ValidationError(
                f"Related object {related_model.__name__} "
                f"with id '{related_id}' was not found."
            )

        return instance

    @staticmethod
    def apply_values(model, instance, values):
        """Применяет значения Excel к импортируемым полям."""

        import_fields = DirectoryImportService.get_import_fields(model)

        for field in import_fields:
            if isinstance(field, models.ForeignKey):
                value_field = f"{field.name}_value"

                if field.name not in values and value_field not in values:
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
