from django.db import transaction


def generate_code(model, field_name, prefix):
    with transaction.atomic():
        last_object = model.objects.select_for_update().order_by("-id").first()

        next_number = 1 if last_object is None else last_object.id + 1

        return f"{prefix}-{next_number:06d}"
