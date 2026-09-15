from decimal import Decimal

from django.db import transaction

from .models import Stock, StockPolicy


class StockError(Exception):
    """Base exception for stock operations."""


class InsufficientStockError(StockError):
    """Raised when requested quantity exceeds available stock."""


class InsufficientReservedStockError(StockError):
    """Raised when requested quantity exceeds reserved stock."""


class InsufficientOnOrderError(StockError):
    """Raised when requested quantity exceeds quantity on order."""


class InsufficientIncomingStockError(StockError):
    """Raised when requested quantity exceeds incoming stock."""


class StockService:
    @staticmethod
    def _validate_positive(quantity):
        quantity = Decimal(quantity)

        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля.")
        return quantity

    @staticmethod
    def _update_status_locked(
        stock: Stock,
        low_stock_threshold: Decimal | None = None,
    ) -> Stock:
        if low_stock_threshold is None:
            policy = StockPolicy.objects.get(id=1)
            low_stock_threshold = policy.low_stock_threshold

        if stock.is_discontinued:
            stock.status = Stock.Status.DISCONTINUED

        elif stock.quantity_available > low_stock_threshold:
            stock.status = Stock.Status.IN_STOCK

        elif stock.quantity_available > 0:
            stock.status = Stock.Status.LOW_STOCK

        elif stock.quantity_incoming > 0 or stock.quantity_on_order > 0:
            stock.status = Stock.Status.ON_ORDER

        else:
            stock.status = Stock.Status.OUT_OF_STOCK

        stock.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return stock

    @staticmethod
    @transaction.atomic
    def update_status(stock_id: int) -> Stock:
        stock = Stock.objects.select_for_update().get(pk=stock_id)

        return StockService._update_status_locked(stock)

    @staticmethod
    @transaction.atomic
    def reserve(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        if stock.quantity_available < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for product "
                f"{stock.product_id} at warehouse "
                f"{stock.warehouse_id}."
            )

        stock.quantity_available -= quantity
        stock.quantity_reserved += quantity

        stock.save(
            update_fields=[
                "quantity_available",
                "quantity_reserved",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock

    @staticmethod
    def release(stock_id, quantity):
        quantity = StockService._validate_positive(quantity)

        with transaction.atomic():
            stock = Stock.objects.select_for_update().get(id=stock_id)

            if stock.quantity_reserved < quantity:
                raise InsufficientReservedStockError(
                    "Недостаточно зарезервированного количества."
                )

            stock.quantity_reserved -= quantity
            stock.quantity_available += quantity

            stock.save(
                update_fields=[
                    "quantity_available",
                    "quantity_reserved",
                    "updated_at",
                ]
            )

            StockService._update_status_locked(stock)

            return stock

    @staticmethod
    @transaction.atomic
    def sell(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        if stock.quantity_reserved < quantity:
            raise InsufficientReservedStockError(
                f"Insufficient reserved stock for product "
                f"{stock.product_id} at warehouse "
                f"{stock.warehouse_id}."
            )

        stock.quantity_reserved -= quantity

        stock.save(
            update_fields=[
                "quantity_reserved",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock

    @staticmethod
    @transaction.atomic
    def receive(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        if stock.quantity_incoming < quantity:
            raise InsufficientIncomingStockError(
                f"Insufficient incoming stock for product "
                f"{stock.product_id} at warehouse "
                f"{stock.warehouse_id}."
            )

        stock.quantity_incoming -= quantity
        stock.quantity_available += quantity

        stock.save(
            update_fields=[
                "quantity_incoming",
                "quantity_available",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock

    @staticmethod
    @transaction.atomic
    def adjustment(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity == 0:
            raise ValueError("Quantity must not be zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        if quantity < 0:
            decrease = abs(quantity)

            if stock.quantity_available < decrease:
                raise InsufficientStockError(
                    f"Insufficient stock for product "
                    f"{stock.product_id} at warehouse "
                    f"{stock.warehouse_id}."
                )

        stock.quantity_available += quantity

        stock.save(
            update_fields=[
                "quantity_available",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock

    @staticmethod
    @transaction.atomic
    def place_order(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        stock.quantity_on_order += quantity

        stock.save(
            update_fields=[
                "quantity_on_order",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock

    @staticmethod
    @transaction.atomic
    def ship_from_supplier(
        stock_id: int,
        quantity: Decimal,
    ) -> Stock:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        stock = Stock.objects.select_for_update().get(pk=stock_id)

        if stock.quantity_on_order < quantity:
            raise InsufficientOnOrderError(
                f"Insufficient quantity on order for product "
                f"{stock.product_id} at warehouse "
                f"{stock.warehouse_id}."
            )

        stock.quantity_on_order -= quantity
        stock.quantity_incoming += quantity

        stock.save(
            update_fields=[
                "quantity_on_order",
                "quantity_incoming",
                "updated_at",
            ]
        )

        StockService._update_status_locked(stock)

        return stock
