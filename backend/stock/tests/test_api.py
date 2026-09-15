from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import (
    Brand,
    Category,
    Execution,
    Group,
    Model,
    Product,
    Series,
    Type,
)
from stock.models import Stock, StockPolicy, Warehouse
from stock.services import StockService


class StockAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="API категория",
        )

        cls.group = Group.objects.create(
            name="API группа",
        )

        cls.brand = Brand.objects.create(
            name="API бренд",
        )

        cls.series = Series.objects.create(
            brand=cls.brand,
            name="API серия",
        )

        cls.type = Type.objects.create(
            name="API тип",
        )

        cls.model = Model.objects.create(
            type=cls.type,
            name="API модель",
        )

        cls.execution = Execution.objects.create(
            type=cls.type,
            name="API исполнение",
        )

        cls.product = Product.objects.create(
            article="API-001",
            category=cls.category,
            group=cls.group,
            brand=cls.brand,
            series=cls.series,
            type=cls.type,
            model=cls.model,
            execution=cls.execution,
            sales_unit="шт",
        )

        cls.warehouse = Warehouse.objects.create(
            code="API-MAIN",
            name="API основной склад",
        )

        cls.stock_policy = StockPolicy.objects.create(
            low_stock_threshold=Decimal("5.000"),
        )

        cls.stock = Stock.objects.create(
            product=cls.product,
            warehouse=cls.warehouse,
            quantity_available=Decimal("10.000"),
            quantity_reserved=Decimal("0.000"),
        )

    def test_stock_list(self):
        response = self.client.get(
            reverse("stock-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.stock.id,
        )

    def test_stock_detail(self):
        response = self.client.get(
            reverse(
                "stock-detail",
                kwargs={"pk": self.stock.id},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.stock.id,
        )
        self.assertEqual(
            response.data["quantity_available"],
            "10.000",
        )

    def test_stock_detail_not_found(self):
        response = self.client.get(
            reverse(
                "stock-detail",
                kwargs={"pk": 999999},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_warehouse_list(self):
        response = self.client.get(
            reverse("warehouse-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.warehouse.id,
        )

    def test_warehouse_detail(self):
        response = self.client.get(
            reverse(
                "warehouse-detail",
                kwargs={"pk": self.warehouse.id},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["code"],
            "API-MAIN",
        )

    def test_reserve_api(self):
        response = self.client.post(
            reverse(
                "stock-reserve",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "3.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("3.000"),
        )

    def test_release_api(self):
        StockService.reserve(
            self.stock.id,
            Decimal("5.000"),
        )

        response = self.client.post(
            reverse(
                "stock-release",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "2.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("3.000"),
        )

    def test_sell_api(self):
        StockService.reserve(
            self.stock.id,
            Decimal("5.000"),
        )

        response = self.client.post(
            reverse(
                "stock-sell",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "2.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("3.000"),
        )

    def test_receive_api(self):
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(
            update_fields=["quantity_incoming"],
        )

        response = self.client.post(
            reverse(
                "stock-receive",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "2.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("12.000"),
        )
        self.assertEqual(
            self.stock.quantity_incoming,
            Decimal("3.000"),
        )

    def test_adjustment_api(self):
        response = self.client.post(
            reverse(
                "stock-adjustment",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "-3.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.000"),
        )

    def test_place_order_api(self):
        response = self.client.post(
            reverse(
                "stock-place-order",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "20.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("20.000"),
        )

    def test_ship_from_supplier_api(self):
        StockService.place_order(
            self.stock.id,
            Decimal("20.000"),
        )

        response = self.client.post(
            reverse(
                "stock-ship-from-supplier",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "8.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("12.000"),
        )
        self.assertEqual(
            self.stock.quantity_incoming,
            Decimal("8.000"),
        )

    def test_update_status_api(self):
        self.stock.quantity_available = Decimal("0.000")
        self.stock.save(
            update_fields=["quantity_available"],
        )

        response = self.client.post(
            reverse(
                "stock-update-status",
                kwargs={"pk": self.stock.id},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.status,
            Stock.Status.OUT_OF_STOCK,
        )

    def test_operation_zero_quantity(self):
        response = self.client.post(
            reverse(
                "stock-reserve",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "0.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_operation_negative_quantity(self):
        response = self.client.post(
            reverse(
                "stock-reserve",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "-1.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reserve_insufficient_stock(self):
        response = self.client.post(
            reverse(
                "stock-reserve",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "11.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("10.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("0.000"),
        )

    def test_operation_stock_not_found(self):
        response = self.client.post(
            reverse(
                "stock-reserve",
                kwargs={"pk": 999999},
            ),
            {
                "quantity": "1.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_stock_quantities_are_read_only(self):
        response = self.client.patch(
            reverse(
                "stock-detail",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity_available": "100.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("10.000"),
        )
    def test_release_insufficient_reserved_stock(self):
        StockService.reserve(
            self.stock.id,
            Decimal("3.000"),
        )

        response = self.client.post(
            reverse(
                "stock-release",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "4.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )


    def test_sell_insufficient_reserved_stock(self):
        StockService.reserve(
            self.stock.id,
            Decimal("3.000"),
        )

        response = self.client.post(
            reverse(
                "stock-sell",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "4.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )


    def test_receive_insufficient_incoming(self):
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(
            update_fields=["quantity_incoming"],
        )

        response = self.client.post(
            reverse(
                "stock-receive",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "6.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )


    def test_ship_from_supplier_insufficient_on_order(self):
        StockService.place_order(
            self.stock.id,
            Decimal("5.000"),
        )

        response = self.client.post(
            reverse(
                "stock-ship-from-supplier",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "6.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )


    def test_adjustment_insufficient_stock(self):
        response = self.client.post(
            reverse(
                "stock-adjustment",
                kwargs={"pk": self.stock.id},
            ),
            {
                "quantity": "-11.000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )


    def test_operation_stock_not_found_for_all_operations(self):
        operations = (
            "stock-reserve",
            "stock-release",
            "stock-sell",
            "stock-receive",
            "stock-place-order",
            "stock-ship-from-supplier",
        )

        for operation in operations:
            with self.subTest(operation=operation):
                response = self.client.post(
                    reverse(
                        operation,
                        kwargs={"pk": 999999},
                    ),
                    {
                        "quantity": "1.000",
                    },
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_404_NOT_FOUND,
                )