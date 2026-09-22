from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import (
    Brand,
    Category,
    Group,
    Product,
    Type,
)
from prices.models import (
    Currency,
    Discount,
    Price,
)

class PriceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_product(self, article="API-001"):
        category = Category.objects.create(
            name="API Category",
        )
        group = Group.objects.create(
            name="API Group",
        )
        brand = Brand.objects.create(
            name="API Brand",
        )
        product_type = Type.objects.create(
            name="API Type",
        )

        return Product.objects.create(
            article=article,
            category=category,
            group=group,
            brand=brand,
            type=product_type,
            sales_unit="pcs",
        )

    def create_currency(self, code="UAH"):
        return Currency.objects.create(
            code=code,
            name="Ukrainian Hryvnia",
            symbol="₴",
        )

    def test_current_price_by_currency(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": "UAH"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], price.id)
        self.assertEqual(
            response.data["amount"],
            "1000.00",
        )

    def test_current_price_by_currency_not_found(self):
        product = self.create_product()
        currency = self.create_currency(code="UAH")

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": "USD"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Валюта не найдена.",
        )

    def test_current_price_requires_currency(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Параметр currency обязателен.",
        )

    def test_current_price_product_not_found(self):
        currency = self.create_currency()

        response = self.client.get(
            "/api/prices/products/999999/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Товар не найден.",
        )

    def test_current_price_not_found(self):
        product = self.create_product()
        currency = self.create_currency()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Текущая цена не найдена.",
        )

    def test_current_price_inactive_currency(self):
        product = self.create_product()

        currency = self.create_currency()
        currency.is_active = False
        currency.save()

        response = self.client.get(
            f"/api/prices/products/{product.id}/current/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Валюта не найдена.",
        )

    def test_calculated_price_without_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product"], product.id)
        self.assertEqual(response.data["currency"], "UAH")
        self.assertEqual(response.data["price"], "1000.00")
        self.assertIsNone(response.data["discount"])
        self.assertIsNone(response.data["discount_type"])
        self.assertEqual(
            response.data["final_price"],
            "1000.00",
        )

    def test_calculated_price_with_percent_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "1000.00")
        self.assertEqual(response.data["discount"], "10.00")
        self.assertEqual(
            response.data["discount_type"],
            "percent",
        )
        self.assertEqual(
            response.data["final_price"],
            "900.00",
        )

    def test_calculated_price_with_fixed_discount(self):
        product = self.create_product()
        currency = self.create_currency()

        Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_FIXED,
            value=Decimal("150.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "1000.00")
        self.assertEqual(response.data["discount"], "150.00")
        self.assertEqual(
            response.data["discount_type"],
            "fixed",
        )
        self.assertEqual(
            response.data["final_price"],
            "850.00",
        )

    def test_calculated_price_requires_currency(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Параметр currency обязателен.",
        )

    def test_calculated_price_not_found(self):
        product = self.create_product()
        currency = self.create_currency()

        response = self.client.get(
            f"/api/prices/products/{product.id}/calculated/",
            {"currency": currency.code},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Текущая цена не найдена.",
        )

    def test_product_price_history(self):
        product = self.create_product()
        currency = self.create_currency()

        price = Price.objects.create(
            product=product,
            currency=currency,
            amount=Decimal("1000.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        discount = Discount.objects.create(
            product=product,
            type=Discount.DISCOUNT_TYPE_PERCENT,
            value=Decimal("10.00"),
            valid_from=datetime(
                2026,
                1,
                1,
                tzinfo=dt_timezone.utc,
            ),
        )

        response = self.client.get(
            f"/api/prices/products/{product.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["product"],
            product.id,
        )

        self.assertEqual(
            len(response.data["prices"]),
            1,
        )
        self.assertEqual(
            response.data["prices"][0]["id"],
            price.id,
        )
        self.assertEqual(
            response.data["prices"][0]["currency"]["code"],
            "UAH",
        )

        self.assertEqual(
            len(response.data["discounts"]),
            1,
        )
        self.assertEqual(
            response.data["discounts"][0]["id"],
            discount.id,
        )
        self.assertEqual(
            response.data["discounts"][0]["type"],
            "percent",
        )

    def test_product_price_history_empty(self):
        product = self.create_product()

        response = self.client.get(
            f"/api/prices/products/{product.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["product"],
            product.id,
        )
        self.assertEqual(
            response.data["prices"],
            [],
        )
        self.assertEqual(
            response.data["discounts"],
            [],
        )

    def test_product_price_history_product_not_found(self):
        response = self.client.get(
            "/api/prices/products/999999/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Товар не найден.",
        )