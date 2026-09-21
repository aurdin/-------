from django.contrib.auth import get_user_model

from catalog.models import (
    Category,
    CategoryGroup,
    Group,
    Product,
    Type,
)
from prices.models import Currency


def create_user(**overrides):
    User = get_user_model()

    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    data.update(overrides)

    password = data.pop("password")

    user = User(**data)
    user.set_password(password)
    user.save()

    return user


def create_currency(**overrides):
    data = {
        "code": "UAH",
        "name": "Ukrainian Hryvnia",
        "symbol": "₴",
        "is_active": True,
    }
    data.update(overrides)

    return Currency.objects.create(**data)


def create_category(**overrides):
    data = {
        "name": "Тестовая категория",
    }
    data.update(overrides)

    return Category.objects.create(**data)


def create_group(**overrides):
    data = {
        "name": "Тестовая группа",
    }
    data.update(overrides)

    return Group.objects.create(**data)


def create_category_group(category=None, group=None, **overrides):
    if category is None:
        category = create_category()

    if group is None:
        group = create_group()

    data = {
        "category": category,
        "group": group,
    }
    data.update(overrides)

    return CategoryGroup.objects.create(**data)


def create_type(**overrides):
    data = {
        "name": "Тестовый тип",
    }
    data.update(overrides)

    return Type.objects.create(**data)


def create_product(
    *,
    category=None,
    group=None,
    type=None,
    **overrides,
):
    if category is None:
        category = create_category()

    if group is None:
        group = create_group()

    CategoryGroup.objects.get_or_create(
        category=category,
        group=group,
    )

    if type is None:
        type = create_type()

    data = {
        "article": "TEST-001",
        "category": category,
        "group": group,
        "type": type,
        "sales_unit": "шт.",
    }
    data.update(overrides)

    return Product.objects.create(**data)
