from rest_framework.test import APITestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection

from catalog.models import (
    Brand,
    Category,
    CategoryGroup,
    Group,
    Product,
    Type,
    Series,
    Model,
    Execution,
    Color,
    Characteristic,
    CharacteristicValue,
    TypeCharacteristic,
    ProductCharacteristic,
)


class ProductListViewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Для дома",
        )

        self.group = Group.objects.create(
            name="Вилки",
        )

        CategoryGroup.objects.create(
            category=self.category,
            group=self.group,
        )

        self.brand = Brand.objects.create(
            name="Legrand",
        )

        self.type = Type.objects.create(
            name="Вилка",
        )

        self.active_product = Product.objects.create(
            article="TEST-001",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        self.number_characteristic = Characteristic.objects.create(
            name="Ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="A",
        )

        self.text_characteristic = Characteristic.objects.create(
            name="Цвет корпуса",
            value_type=Characteristic.VALUE_TYPE_TEXT,
        )

        self.boolean_characteristic = Characteristic.objects.create(
            name="С заземлением",
            value_type=Characteristic.VALUE_TYPE_BOOLEAN,
        )

        self.reference_characteristic = Characteristic.objects.create(
            name="Напряжение",
            value_type=Characteristic.VALUE_TYPE_REFERENCE,
        )

        self.reference_value = CharacteristicValue.objects.create(
            characteristic=self.reference_characteristic,
            value="230",
        )

        TypeCharacteristic.objects.create(
            type=self.type,
            characteristic=self.number_characteristic,
        )

        TypeCharacteristic.objects.create(
            type=self.type,
            characteristic=self.text_characteristic,
        )

        TypeCharacteristic.objects.create(
            type=self.type,
            characteristic=self.boolean_characteristic,
        )

        TypeCharacteristic.objects.create(
            type=self.type,
            characteristic=self.reference_characteristic,
        )

        ProductCharacteristic.objects.create(
            product=self.active_product,
            characteristic=self.number_characteristic,
            value_number=16,
        )

        ProductCharacteristic.objects.create(
            product=self.active_product,
            characteristic=self.text_characteristic,
            value_text="black",
        )

        ProductCharacteristic.objects.create(
            product=self.active_product,
            characteristic=self.boolean_characteristic,
            value_boolean=True,
        )

        ProductCharacteristic.objects.create(
            product=self.active_product,
            characteristic=self.reference_characteristic,
            value_reference=self.reference_value,
        )        

        self.inactive_product = Product.objects.create(
            article="TEST-002",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=False,
        )

    def test_get_products_returns_active_products(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-002", articles)

    def test_get_products_does_not_have_n_plus_one_queries(self):
        with CaptureQueriesContext(connection) as context:
            response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)

        self.assertLessEqual(
            len(context.captured_queries),
            10,
        )

    def test_filter_by_category(self):
        second_category = Category.objects.create(
            name="Для улицы",
        )

        second_group = Group.objects.create(
            name="Розетки",
        )

        CategoryGroup.objects.create(
            category=second_category,
            group=second_group,
        )

        Product.objects.create(
            article="TEST-003",
            category=second_category,
            group=second_group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?category={self.category.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-003", articles)

    def test_filter_by_group(self):
        second_group = Group.objects.create(
            name="Розетки",
        )

        CategoryGroup.objects.create(
            category=self.category,
            group=second_group,
        )

        Product.objects.create(
            article="TEST-004",
            category=self.category,
            group=second_group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?group={self.group.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-004", articles)

    def test_filter_by_brand(self):
        second_brand = Brand.objects.create(
            name="Schneider Electric",
        )

        Product.objects.create(
            article="TEST-005",
            category=self.category,
            group=self.group,
            brand=second_brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?brand={self.brand.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-005", articles)

    def test_filter_by_series(self):
        second_series = Series.objects.create(
            name="Valena",
            brand=self.brand,
        )

        Product.objects.create(
            article="TEST-006",
            category=self.category,
            group=self.group,
            brand=self.brand,
            series=second_series,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?series={second_series.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-006", articles)
        self.assertNotIn("TEST-001", articles)

    def test_filter_by_type(self):
        second_type = Type.objects.create(
            name="Розетка",
        )

        Product.objects.create(
            article="TEST-007",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=second_type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?type={self.type.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-007", articles)

    def test_filter_by_model(self):
        second_model = Model.objects.create(
            name="Розеточная",
            type=self.type,
        )

        Product.objects.create(
            article="TEST-008",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            model=second_model,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?model={second_model.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-008", articles)
        self.assertNotIn("TEST-001", articles)

    def test_filter_by_execution(self):
        second_execution = Execution.objects.create(
            name="С заземлением",
            type=self.type,
        )

        Product.objects.create(
            article="TEST-009",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            execution=second_execution,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?execution={second_execution.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-009", articles)
        self.assertNotIn("TEST-001", articles)

    def test_filter_by_color(self):
        first_color = Color.objects.create(
            name="Черный",
        )

        second_color = Color.objects.create(
            name="Белый",
        )

        self.active_product.color = first_color
        self.active_product.save()

        Product.objects.create(
            article="TEST-010",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            color=second_color,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?color={first_color.id}")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-010", articles)

    def test_filter_by_protection_degree(self):
        self.active_product.protection_degree = "IP44"
        self.active_product.save()

        Product.objects.create(
            article="TEST-011",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            protection_degree="IP20",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?protection_degree=IP44")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-011", articles)

    def test_filter_by_article(self):
        Product.objects.create(
            article="TEST-012",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?article=TEST-012")

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-012", articles)
        self.assertNotIn("TEST-001", articles)

    def test_filter_by_type_and_color(self):
        first_color = Color.objects.create(
            name="Черный",
        )

        second_color = Color.objects.create(
            name="Белый",
        )

        self.active_product.color = first_color
        self.active_product.save()

        Product.objects.create(
            article="TEST-013",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            color=second_color,
            sales_unit="шт.",
            status=True,
        )

        second_type = Type.objects.create(
            name="Розетка",
        )

        Product.objects.create(
            article="TEST-014",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=second_type,
            color=first_color,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(
            f"/api/products/?type={self.type.id}&color={first_color.id}"
        )

        self.assertEqual(response.status_code, 200)

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-001", articles)
        self.assertNotIn("TEST-013", articles)
        self.assertNotIn("TEST-014", articles)

    def test_search_by_article(self):
        Product.objects.create(
            article="LEGRAND-123",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=LEGRAND-123")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("LEGRAND-123", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_type(self):
        second_type = Type.objects.create(name="Розетка")

        Product.objects.create(
            article="TEST-SEARCH-TYPE",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=second_type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=розетка")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-TYPE", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_brand(self):
        second_brand = Brand.objects.create(name="Schneider")

        Product.objects.create(
            article="TEST-SEARCH-BRAND",
            category=self.category,
            group=self.group,
            brand=second_brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=schneider")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-BRAND", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_series(self):
        series = Series.objects.create(
            name="Valena",
            brand=self.brand,
        )

        Product.objects.create(
            article="TEST-SEARCH-SERIES",
            category=self.category,
            group=self.group,
            brand=self.brand,
            series=series,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=valena")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-SERIES", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_category(self):
        second_category = Category.objects.create(name="Для улицы")
        CategoryGroup.objects.create(
            category=second_category,
            group=self.group,
        )

        Product.objects.create(
            article="TEST-SEARCH-CATEGORY",
            category=second_category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=улицы")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-CATEGORY", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_group(self):
        second_group = Group.objects.create(name="Розетки")
        CategoryGroup.objects.create(
            category=self.category,
            group=second_group,
        )

        Product.objects.create(
            article="TEST-SEARCH-GROUP",
            category=self.category,
            group=second_group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=розетки")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-GROUP", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_color(self):
        color = Color.objects.create(name="Черный")

        Product.objects.create(
            article="TEST-SEARCH-COLOR",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            color=color,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=черный")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-COLOR", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_protection_degree(self):
        Product.objects.create(
            article="TEST-SEARCH-IP",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            protection_degree="IP44",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=IP44")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-IP", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_barcode(self):
        Product.objects.create(
            article="TEST-SEARCH-BARCODE",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            barcode="4820001234567",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=4820001234567")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-BARCODE", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_packaging(self):
        Product.objects.create(
            article="TEST-SEARCH-PACKAGING",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            packaging="Коробка 10 шт.",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=коробка")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-PACKAGING", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_manufacturer_name(self):
        Product.objects.create(
            article="TEST-SEARCH-MANUFACTURER",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            manufacturer_name="Legrand France",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=france")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-MANUFACTURER", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_by_manufacturer_description(self):
        Product.objects.create(
            article="TEST-SEARCH-DESCRIPTION",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            manufacturer_description="Промышленная электрическая вилка",
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=промышленная")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-DESCRIPTION", articles)
        self.assertNotIn("TEST-001", articles)

    def test_search_is_case_insensitive_and_partial(self):
        Product.objects.create(
            article="LEGRAND-ABC",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get("/api/products/?search=grand")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("LEGRAND-ABC", articles)

    def test_search_ignores_filters(self):
        second_type = Type.objects.create(name="Розетка")

        Product.objects.create(
            article="TEST-SEARCH-IGNORE-FILTER",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=second_type,
            sales_unit="шт.",
            status=True,
        )

        response = self.client.get(f"/api/products/?search=розетка&type={self.type.id}")

        articles = [item["article"] for item in response.data["results"]]

        self.assertIn("TEST-SEARCH-IGNORE-FILTER", articles)

    def test_search_no_results_returns_message(self):
               
        response = self.client.get("/api/products/?search=товар-которого-нет")


        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(
            response.data["message"],
            "Товары не найдены.",
        )

    def test_filter_by_characteristic_number(self):
        response = self.client.get(
            "/api/products/",
            {"characteristic": f"{self.number_characteristic.id}:16"},
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_filter_by_characteristic_text(self):
        response = self.client.get(
            "/api/products/",
            {"characteristic": f"{self.text_characteristic.id}:black"},
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_filter_by_characteristic_boolean(self):
        response = self.client.get(
            "/api/products/",
            {"characteristic": f"{self.boolean_characteristic.id}:true"},
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_filter_by_characteristic_reference(self):
        response = self.client.get(
            "/api/products/",
            {"characteristic": f"{self.reference_characteristic.id}:230"},
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_filter_by_multiple_characteristics_uses_and(self):
        response = self.client.get(
            "/api/products/",
            {
                "characteristic": [
                    f"{self.number_characteristic.id}:16",
                    f"{self.text_characteristic.id}:black",
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_search_has_priority_over_characteristic_filter(self):
        response = self.client.get(
            "/api/products/",
            {
                "search": self.active_product.article,
                "characteristic": f"{self.number_characteristic.id}:999",
            },
        )

        self.assertEqual(response.status_code, 200)
        articles = {product["article"] for product in response.data["results"]}

        self.assertIn(self.active_product.article, articles)

    def test_characteristic_filter_no_results_returns_message(self):
        response = self.client.get(
            "/api/products/",
            {"characteristic": f"{self.number_characteristic.id}:999999"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(
            response.data["message"],
            "Товары не найдены.",
        ) 

class ProductDetailViewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Для дома",
        )

        self.group = Group.objects.create(
            name="Вилки",
        )

        CategoryGroup.objects.create(
            category=self.category,
            group=self.group,
        )

        self.brand = Brand.objects.create(
            name="Legrand",
        )

        self.type = Type.objects.create(
            name="Вилка",
        )

        self.product = Product.objects.create(
            article="TEST-DETAIL-001",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        self.inactive_product = Product.objects.create(
            article="TEST-DETAIL-002",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=False,
        )    

    def test_get_active_product(self):
        response = self.client.get(f"/api/products/{self.product.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.product.id)
        self.assertEqual(response.data["article"], "TEST-DETAIL-001")
        self.assertEqual(response.data["status"], True)

    def test_get_inactive_product_returns_404(self):
        response = self.client.get(f"/api/products/{self.inactive_product.id}/")

        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_product_returns_404(self):
        response = self.client.get("/api/products/999999/")

        self.assertEqual(response.status_code, 404)

class CatalogFiltersViewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Для дома",
        )

        self.group = Group.objects.create(
            name="Вилки",
        )

        CategoryGroup.objects.create(
            category=self.category,
            group=self.group,
        )

        self.brand = Brand.objects.create(
            name="Legrand",
        )

        self.type = Type.objects.create(
            name="Вилка",
        )

        self.unused_category = Category.objects.create(
            name="Неиспользуемая категория",
        )

        self.product = Product.objects.create(
            article="TEST-FILTER-001",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        Product.objects.create(
            article="TEST-FILTER-002",
            category=self.unused_category,
            group=self.group,
            type=self.type,
            sales_unit="шт.",
            status=False,
        )

    def test_returns_only_values_used_by_active_products(self):
        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["categories"],
            [
                {
                    "id": self.category.id,
                    "name": "Для дома",
                }
            ],
        )

        self.assertEqual(
            response.data["groups"],
            [
                {
                    "id": self.group.id,
                    "name": "Вилки",
                }
            ],
        )

        self.assertEqual(
            response.data["brands"],
            [
                {
                    "id": self.brand.id,
                    "name": "Legrand",
                }
            ],
        )

        self.assertEqual(
            response.data["types"],
            [
                {
                    "id": self.type.id,
                    "name": "Вилка",
                }
            ],
        )

        self.assertNotIn(
            {
                "id": self.unused_category.id,
                "name": "Неиспользуемая категория",
            },
            response.data["categories"],
        )

    def test_returns_all_expected_keys(self):
        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            set(response.data.keys()),
            {
                "categories",
                "groups",
                "brands",
                "series",
                "types",
                "models",
                "executions",
                "colors",
                "characteristics",
            },
        )

    def test_returns_active_product_characteristics(self):
        characteristic = Characteristic.objects.create(
            name="Ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="A",
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=characteristic,
            value_number=16,
            status=True,
        )

        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["characteristics"],
            [
                {
                    "id": characteristic.id,
                    "name": "Ток",
                    "value_type": "number",
                    "unit": "A",
                    "values": [
                        {
                            "value": "16",
                        }
                    ],
                }
            ],
        )

    def test_excludes_inactive_product_characteristics(self):
        characteristic = Characteristic.objects.create(
            name="Ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="A",
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=characteristic,
            value_number=16,
            status=False,
        )

        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["characteristics"],
            [],
        ) 
        
    def test_returns_characteristic_values(self):
        number_characteristic = Characteristic.objects.create(
            name="Ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="A",
        )

        text_characteristic = Characteristic.objects.create(
            name="Материал",
            value_type=Characteristic.VALUE_TYPE_TEXT,
        )

        boolean_characteristic = Characteristic.objects.create(
            name="С заземлением",
            value_type=Characteristic.VALUE_TYPE_BOOLEAN,
        )

        reference_characteristic = Characteristic.objects.create(
            name="Напряжение",
            value_type=Characteristic.VALUE_TYPE_REFERENCE,
            unit="V",
        )

        voltage_220 = CharacteristicValue.objects.create(
            characteristic=reference_characteristic,
            value="220",
        )

        voltage_230 = CharacteristicValue.objects.create(
            characteristic=reference_characteristic,
            value="230",
        )

        product_2 = Product.objects.create(
            article="TEST-FILTER-003",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        product_3 = Product.objects.create(
            article="TEST-FILTER-004",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=number_characteristic,
            value_number=10,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=product_2,
            characteristic=number_characteristic,
            value_number=16,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=product_3,
            characteristic=number_characteristic,
            value_number=25,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=text_characteristic,
            value_text="black",
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=product_2,
            characteristic=text_characteristic,
            value_text="white",
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=boolean_characteristic,
            value_boolean=True,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=product_2,
            characteristic=boolean_characteristic,
            value_boolean=False,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=self.product,
            characteristic=reference_characteristic,
            value_reference=voltage_220,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=product_2,
            characteristic=reference_characteristic,
            value_reference=voltage_230,
            status=True,
        )

        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)

        characteristics = {item["name"]: item for item in response.data["characteristics"]}

        self.assertEqual(
            characteristics["Ток"]["values"],
            [
                {"value": "10"},
                {"value": "16"},
                {"value": "25"},
            ],
        )

        self.assertEqual(
            characteristics["Материал"]["values"],
            [
                {"value": "black"},
                {"value": "white"},
            ],
        )

        self.assertEqual(
            characteristics["С заземлением"]["values"],
            [
                {"value": "false"},
                {"value": "true"},
            ],
        )

        self.assertEqual(
            characteristics["Напряжение"]["values"],
            [
                {"value": "220"},
                {"value": "230"},
            ],
        )  
        
    def test_excludes_inactive_characteristic_values(self):
        characteristic = Characteristic.objects.create(
            name="Ток",
            value_type=Characteristic.VALUE_TYPE_NUMBER,
            unit="A",
        )

        active_product = Product.objects.create(
            article="TEST-FILTER-005",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        inactive_product = Product.objects.create(
            article="TEST-FILTER-006",
            category=self.category,
            group=self.group,
            brand=self.brand,
            type=self.type,
            sales_unit="шт.",
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=active_product,
            characteristic=characteristic,
            value_number=16,
            status=True,
        )

        ProductCharacteristic.objects.create(
            product=inactive_product,
            characteristic=characteristic,
            value_number=25,
            status=False,
        )

        response = self.client.get("/api/catalog/filters/")

        self.assertEqual(response.status_code, 200)

        characteristics = {
            item["name"]: item
            for item in response.data["characteristics"]
        }

        self.assertEqual(
            characteristics["Ток"]["values"],
            [
                {"value": "16"},
            ],
        )                                                                                       