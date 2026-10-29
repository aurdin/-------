import csv
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from zipfile import BadZipFile

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import CharField
from django.db.models.functions import Trim, Upper
from django.utils import timezone
from django.utils.translation import gettext as _
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from apps.prices.models import Prices
from apps.prices.services import normalize_article


class WorkbookImportError(Exception):
    pass


def _parse_amount(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(_("Amount is required."))
    if isinstance(value, bool):
        raise ValueError(_("Amount must be a valid number."))

    try:
        if isinstance(value, str):
            raw_value = value.strip()
            if "," in raw_value and "." in raw_value:
                raise ValueError(_("Amount must use either a decimal comma or a decimal point."))
            amount = Decimal(raw_value.replace(",", "."))
        else:
            amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("Amount"):
            raise
        raise ValueError(_("Amount must be a valid number.")) from exc

    if not amount.is_finite():
        raise ValueError(_("Amount must be a valid number."))
    if amount < 0:
        raise ValueError(_("Negative prices are not allowed."))

    try:
        rounded_amount = amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(_("Amount exceeds the supported precision.")) from exc
    if rounded_amount != amount:
        raise ValueError(_("Amount may not have more than two decimal places."))

    try:
        return Prices._meta.get_field("amount").clean(rounded_amount, None)
    except ValidationError as exc:
        raise ValueError(" ".join(str(message) for message in exc.messages)) from exc


def _catalog_article_keys(article_keys):
    try:
        product_model = apps.get_model("catalog", "Product")
    except LookupError:
        return None

    try:
        product_model._meta.get_field("article")
    except FieldDoesNotExist:
        return None

    return set(
        product_model.objects.annotate(
            _article_key=Upper(Trim("article", output_field=CharField()))
        )
        .filter(_article_key__in=article_keys)
        .values_list("_article_key", flat=True)
    )


def _analyze_rows(header_row, numbered_rows, valid_from):
    if not header_row:
        raise WorkbookImportError(_("The input file is empty."))

    headers = {}
    for column_number, value in enumerate(header_row):
        if value is not None:
            key = str(value).strip().lstrip("\ufeff").casefold()
            if key:
                headers.setdefault(key, column_number)

    if any(name not in headers for name in ("article", "amount")):
        raise WorkbookImportError(
            _("Required columns are missing: article and amount.")
        )

    rows = []
    article_rows = {}
    for row_number, values in numbered_rows:
        if not any(value is not None and str(value).strip() for value in values):
            continue

        article_index = headers["article"]
        amount_index = headers["amount"]
        article_value = values[article_index] if article_index < len(values) else None
        amount_value = values[amount_index] if amount_index < len(values) else None
        article = str(article_value).strip() if article_value is not None else ""
        article_key = normalize_article(article)
        errors = []

        if not article_key:
            errors.append(_("Article is required."))
        else:
            article_rows.setdefault(article_key, []).append(row_number)

        try:
            amount = _parse_amount(amount_value)
        except ValueError as exc:
            amount = None
            errors.append(str(exc))

        rows.append(
            {
                "row_number": row_number,
                "article": article,
                "article_key": article_key,
                "amount": str(amount) if amount is not None else str(amount_value or ""),
                "errors": errors,
            }
        )

    if not rows:
        raise WorkbookImportError(_("The input file contains no data rows."))

    batch_errors = []
    if valid_from < timezone.localdate():
        batch_errors.append(_("Start date cannot be earlier than today."))

    duplicates = [
        {"article": key, "row_numbers": row_numbers}
        for key, row_numbers in article_rows.items()
        if len(row_numbers) > 1
    ]
    for duplicate in duplicates:
        duplicate_message = _("Duplicate article in rows %(rows)s.") % {
            "rows": ", ".join(str(number) for number in duplicate["row_numbers"])
        }
        for row in rows:
            if row["article_key"] == duplicate["article"]:
                row["errors"].append(duplicate_message)

    article_keys = {row["article_key"] for row in rows if row["article_key"]}
    known_article_keys = _catalog_article_keys(article_keys)
    catalog_check_available = known_article_keys is not None
    if catalog_check_available:
        for row in rows:
            if row["article_key"] and row["article_key"] not in known_article_keys:
                row["errors"].append(_("Article was not found in the product catalog."))

    valid_rows = [row for row in rows if not row["errors"]]
    error_count = sum(bool(row["errors"]) for row in rows)
    return {
        "total_rows": len(rows),
        "valid_count": len(valid_rows),
        "error_count": error_count,
        "rows": rows,
        "valid_rows": valid_rows,
        "duplicates": duplicates,
        "batch_errors": batch_errors,
        "catalog_check_available": catalog_check_available,
        "can_confirm": not batch_errors and not duplicates and bool(valid_rows),
    }


def analyze_workbook(content, valid_from=None):
    valid_from = valid_from or timezone.localdate()
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError) as exc:
        raise WorkbookImportError(_("The uploaded file is not a valid XLSX workbook.")) from exc

    try:
        worksheet = workbook.active
        header_row = next(
            worksheet.iter_rows(min_row=1, max_row=1, values_only=True),
            None,
        )
        numbered_rows = enumerate(
            worksheet.iter_rows(min_row=2, values_only=True),
            start=2,
        )
        return _analyze_rows(header_row, numbered_rows, valid_from)
    finally:
        workbook.close()


def analyze_csv(content, valid_from=None):
    valid_from = valid_from or timezone.localdate()
    try:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1251")
        sample = "\n".join(text.splitlines()[:10])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
            reader = csv.reader(StringIO(text), delimiter=delimiter)
        else:
            reader = csv.reader(StringIO(text), dialect)
        rows = iter(reader)
        header_row = next(rows, None)
        numbered_rows = enumerate(rows, start=2)
        return _analyze_rows(header_row, numbered_rows, valid_from)
    except (csv.Error, UnicodeError, LookupError) as exc:
        raise WorkbookImportError(_("The uploaded file is not a valid CSV file.")) from exc


def analyze_import_file(content, valid_from, file_format):
    if file_format == "xlsx":
        return analyze_workbook(content, valid_from)
    if file_format == "csv":
        return analyze_csv(content, valid_from)
    raise WorkbookImportError(_("Unsupported import file format."))


