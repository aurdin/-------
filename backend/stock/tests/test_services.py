from decimal import Decimal

from django.test import TestCase

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

from stock.services import (
    InsufficientIncomingStockError,
    InsufficientOnOrderError,
    InsufficientReservedStockError,
    InsufficientStockError,
    StockService,
)


class StockServiceReserveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Тестовая категория",
        )

        cls.group = Group.objects.create(
            name="Тестовая группа",
        )

        cls.brand = Brand.objects.create(
            name="Тестовый бренд",
        )

        cls.series = Series.objects.create(
            brand=cls.brand,
            name="Тестовая серия",
        )

        cls.type = Type.objects.create(
            name="Тестовый тип",
        )

        cls.model = Model.objects.create(
            type=cls.type,
            name="Тестовая модель",
        )

        cls.execution = Execution.objects.create(
            type=cls.type,
            name="Тестовое исполнение",
        )

        cls.product = Product.objects.create(
            article="TEST-001",
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
            code="MAIN",
            name="Основной склад",
        )

        cls.stock_policy = StockPolicy.objects.create(
            id=1,
            low_stock_threshold=Decimal("5.000"),
        )

        cls.stock = Stock.objects.create(
            product=cls.product,
            warehouse=cls.warehouse,
            quantity_available=Decimal("10.000"),
            quantity_reserved=Decimal("0.000"),
        )

    def test_reserve_success(self):
        StockService.reserve(
            self.stock.id,
            Decimal("3.000"),
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

    def test_reserve_fractional_quantity(self):
        StockService.reserve(
            self.stock.id,
            Decimal("2.500"),
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.500"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("2.500"),
        )

    def test_reserve_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            StockService.reserve(
                self.stock.id,
                Decimal("11.000"),
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

    def test_reserve_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.reserve(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_reserve_negative_quantity(self):
        with self.assertRaises(ValueError):
            StockService.reserve(
                self.stock.id,
                Decimal("-1.000"),
            )

    def test_release_success(self):
        StockService.reserve(self.stock.id, Decimal("5.000"))

        StockService.release(self.stock.id, Decimal("2.000"))

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("3.000"),
        )

    def test_release_fractional_quantity(self):
        StockService.reserve(self.stock.id, Decimal("5.000"))

        StockService.release(self.stock.id, Decimal("2.500"))

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.500"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("2.500"),
        )

    def test_release_insufficient_reserved_stock(self):
        StockService.reserve(self.stock.id, Decimal("3.000"))

        with self.assertRaises(InsufficientReservedStockError):
            StockService.release(
                self.stock.id,
                Decimal("4.000"),
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

    def test_release_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.release(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_release_negative_quantity(self):
        with self.assertRaises(ValueError):
            StockService.release(
                self.stock.id,
                Decimal("-1.000"),
            )

    def test_sell_success(self):
        StockService.reserve(self.stock.id, Decimal("5.000"))

        StockService.sell(self.stock.id, Decimal("2.000"))

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("5.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("3.000"),
        )

    def test_sell_fractional_quantity(self):
        StockService.reserve(self.stock.id, Decimal("5.000"))

        StockService.sell(self.stock.id, Decimal("2.500"))

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("5.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("2.500"),
        )

    def test_sell_insufficient_reserved_stock(self):
        StockService.reserve(self.stock.id, Decimal("3.000"))

        with self.assertRaises(InsufficientReservedStockError):
            StockService.sell(
                self.stock.id,
                Decimal("4.000"),
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

    def test_sell_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.sell(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_sell_negative_quantity(self):
        with self.assertRaises(ValueError):
            StockService.sell(
                self.stock.id,
                Decimal("-1.000"),
            )

    ######################
    def test_receive_success(self):
        self.stock.quantity_incoming = Decimal("8.000")
        self.stock.save(update_fields=["quantity_incoming"])

        StockService.receive(self.stock.id, Decimal("6.000"))

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_available, Decimal("16.000"))
        self.assertEqual(self.stock.quantity_incoming, Decimal("2.000"))

    def test_receive_fractional_quantity(self):
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(update_fields=["quantity_incoming"])

        StockService.receive(self.stock.id, Decimal("2.500"))

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_available, Decimal("12.500"))
        self.assertEqual(self.stock.quantity_incoming, Decimal("2.500"))

    def test_receive_does_not_change_reserved(self):
        self.stock.quantity_reserved = Decimal("3.000")
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(
            update_fields=[
                "quantity_reserved",
                "quantity_incoming",
            ]
        )

        StockService.receive(self.stock.id, Decimal("2.000"))

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_available, Decimal("12.000"))
        self.assertEqual(self.stock.quantity_reserved, Decimal("3.000"))
        self.assertEqual(self.stock.quantity_incoming, Decimal("3.000"))

    def test_receive_insufficient_incoming(self):
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(update_fields=["quantity_incoming"])
        with self.assertRaises(InsufficientIncomingStockError):
            StockService.receive(self.stock.id, Decimal("6.000"))

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_available, Decimal("10.000"))
        self.assertEqual(self.stock.quantity_incoming, Decimal("5.000"))

    def test_receive_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.receive(self.stock.id, Decimal("0.000"))

    #######################

    def test_reserve_updates_status(self):
        self.stock.quantity_available = Decimal("6.000")
        self.stock.status = Stock.Status.IN_STOCK
        self.stock.save(
            update_fields=[
                "quantity_available",
                "status",
            ]
        )

        StockService.reserve(
            self.stock.id,
            Decimal("2.000"),
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity_available,
            Decimal("4.000"),
        )
        self.assertEqual(
            self.stock.quantity_reserved,
            Decimal("2.000"),
        )
        self.assertEqual(
            self.stock.status,
            Stock.Status.LOW_STOCK,
        )

    def test_adjustment_increase(self):
        StockService.adjustment(
            self.stock.id,
            Decimal("5.000"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("15.000"),
        )

    def test_adjustment_decrease(self):
        StockService.adjustment(
            self.stock.id,
            Decimal("-3.000"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("7.000"),
        )

    def test_adjustment_fractional_quantity(self):
        StockService.adjustment(
            self.stock.id,
            Decimal("2.500"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("12.500"),
        )

    def test_adjustment_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            StockService.adjustment(
                self.stock.id,
                Decimal("-11.000"),
            )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_available,
            Decimal("10.000"),
        )

    def test_adjustment_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.adjustment(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_place_order_success(self):
        StockService.place_order(
            self.stock.id,
            Decimal("20.000"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("20.000"),
        )

    def test_place_order_fractional_quantity(self):
        StockService.place_order(
            self.stock.id,
            Decimal("2.500"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("2.500"),
        )

    def test_place_order_accumulates_quantity(self):
        StockService.place_order(
            self.stock.id,
            Decimal("10.000"),
        )
        StockService.place_order(
            self.stock.id,
            Decimal("5.000"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("15.000"),
        )

    def test_place_order_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.place_order(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_place_order_negative_quantity(self):
        with self.assertRaises(ValueError):
            StockService.place_order(
                self.stock.id,
                Decimal("-1.000"),
            )

    def test_ship_from_supplier_success(self):
        StockService.place_order(
            self.stock.id,
            Decimal("20.000"),
        )

        StockService.ship_from_supplier(
            self.stock.id,
            Decimal("8.000"),
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

    def test_ship_from_supplier_fractional_quantity(self):
        StockService.place_order(
            self.stock.id,
            Decimal("10.000"),
        )

        StockService.ship_from_supplier(
            self.stock.id,
            Decimal("2.500"),
        )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("7.500"),
        )
        self.assertEqual(
            self.stock.quantity_incoming,
            Decimal("2.500"),
        )

    def test_ship_from_supplier_accumulates_incoming(self):
        StockService.place_order(
            self.stock.id,
            Decimal("20.000"),
        )

        StockService.ship_from_supplier(
            self.stock.id,
            Decimal("5.000"),
        )
        StockService.ship_from_supplier(
            self.stock.id,
            Decimal("3.000"),
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

    def test_ship_from_supplier_insufficient_on_order(self):
        StockService.place_order(
            self.stock.id,
            Decimal("5.000"),
        )

        with self.assertRaises(InsufficientOnOrderError):
            StockService.ship_from_supplier(
                self.stock.id,
                Decimal("6.000"),
            )

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.quantity_on_order,
            Decimal("5.000"),
        )
        self.assertEqual(
            self.stock.quantity_incoming,
            Decimal("0.000"),
        )

    def test_ship_from_supplier_zero_quantity(self):
        with self.assertRaises(ValueError):
            StockService.ship_from_supplier(
                self.stock.id,
                Decimal("0.000"),
            )

    def test_status_discontinued(self):
        self.stock.is_discontinued = True
        self.stock.quantity_available = Decimal("100.000")
        self.stock.save(
            update_fields=[
                "is_discontinued",
                "quantity_available",
            ]
        )

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.DISCONTINUED,
        )

    def test_status_in_stock(self):
        self.stock.quantity_available = Decimal("10.000")
        self.stock.save(update_fields=["quantity_available"])

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.IN_STOCK,
        )

    def test_status_low_stock(self):
        self.stock.quantity_available = Decimal("5.000")
        self.stock.save(update_fields=["quantity_available"])

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.LOW_STOCK,
        )

    def test_status_uses_stock_policy_threshold(self):
        self.stock_policy.low_stock_threshold = Decimal("10.000")
        self.stock_policy.save(update_fields=["low_stock_threshold"])

        self.stock.quantity_available = Decimal("7.000")
        self.stock.save(update_fields=["quantity_available"])

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.status,
            Stock.Status.LOW_STOCK,
        )

    def test_status_on_order_when_incoming_exists(self):
        self.stock.quantity_available = Decimal("0.000")
        self.stock.quantity_incoming = Decimal("5.000")
        self.stock.save(
            update_fields=[
                "quantity_available",
                "quantity_incoming",
            ]
        )

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.ON_ORDER,
        )

    def test_status_on_order_when_on_order_exists(self):
        self.stock.quantity_available = Decimal("0.000")
        self.stock.quantity_on_order = Decimal("5.000")
        self.stock.save(
            update_fields=[
                "quantity_available",
                "quantity_on_order",
            ]
        )

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.ON_ORDER,
        )

    def test_status_out_of_stock(self):
        self.stock.quantity_available = Decimal("0.000")
        self.stock.quantity_incoming = Decimal("0.000")
        self.stock.quantity_on_order = Decimal("0.000")
        self.stock.save(
            update_fields=[
                "quantity_available",
                "quantity_incoming",
                "quantity_on_order",
            ]
        )

        StockService.update_status(self.stock.id)

        self.stock.refresh_from_db()
        self.assertEqual(
            self.stock.status,
            Stock.Status.OUT_OF_STOCK,
        )
