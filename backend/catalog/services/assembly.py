from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import AssemblyComponent


def validate_assembly_dependency(
    assembly_product_id,
    component_product_id,
):
    if assembly_product_id == component_product_id:
        raise ValidationError(
            {
                "component_product": (
                    "Assembly product cannot be its own component."
                )
            }
        )

    visited = set()
    stack = [component_product_id]

    while stack:
        current_product_id = stack.pop()

        if current_product_id in visited:
            continue

        visited.add(current_product_id)

        if current_product_id == assembly_product_id:
            raise ValidationError(
                {
                    "component_product": (
                        "Circular dependency detected between "
                        "assembly products."
                    )
                }
            )

        next_product_ids = (
            AssemblyComponent.objects
            .filter(assembly_product_id=current_product_id)
            .values_list("component_product_id", flat=True)
        )

        stack.extend(next_product_ids)


@transaction.atomic
def add_component(
    assembly_product,
    component_product,
    quantity,
):
    component = AssemblyComponent(
        assembly_product=assembly_product,
        component_product=component_product,
        quantity=quantity,
    )

    component.full_clean()
    component.save()

    return component