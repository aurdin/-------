from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Stock, Warehouse
from .serializers import (
    StockAdjustmentSerializer,
    StockOperationSerializer,
    StockSerializer,
    WarehouseSerializer,
)
from .services import (
    InsufficientIncomingStockError,
    InsufficientOnOrderError,
    InsufficientReservedStockError,
    InsufficientStockError,
    StockService,
)


class WarehouseListView(APIView):
    def get(self, request):
        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)


class WarehouseDetailView(APIView):
    def get(self, request, pk):
        try:
            warehouse = Warehouse.objects.get(pk=pk)
        except Warehouse.DoesNotExist:
            return Response(
                {"detail": "Склад не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WarehouseSerializer(warehouse)
        return Response(serializer.data)


class StockListView(APIView):
    def get(self, request):
        stocks = Stock.objects.select_related(
            "product",
            "warehouse",
        ).all()

        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)


class StockDetailView(APIView):
    def get(self, request, pk):
        try:
            stock = Stock.objects.select_related(
                "product",
                "warehouse",
            ).get(pk=pk)
        except Stock.DoesNotExist:
            return Response(
                {"detail": "Остаток не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StockSerializer(stock)
        return Response(serializer.data)


class StockOperationView(APIView):
    operation = None

    def post(self, request, pk):
        serializer = StockOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            stock = Stock.objects.get(pk=pk)

            operation_method = getattr(
                StockService,
                self.operation,
            )

            stock = operation_method(
                stock.id,
                serializer.validated_data["quantity"],
            )

        except Stock.DoesNotExist:
            return Response(
                {"detail": "Остаток не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except (
            InsufficientStockError,
            InsufficientReservedStockError,
            InsufficientIncomingStockError,
            InsufficientOnOrderError,
        ) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            StockSerializer(stock).data,
            status=status.HTTP_200_OK,
        )


class StockAdjustmentView(APIView):
    def post(self, request, pk):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            stock = StockService.adjustment(
                pk,
                serializer.validated_data["quantity"],
            )

        except Stock.DoesNotExist:
            return Response(
                {"detail": "Остаток не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except InsufficientStockError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            StockSerializer(stock).data,
            status=status.HTTP_200_OK,
        )


class StockStatusView(APIView):
    def post(self, request, pk):
        try:
            stock = StockService.update_status(pk)

        except Stock.DoesNotExist:
            return Response(
                {"detail": "Остаток не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            StockSerializer(stock).data,
            status=status.HTTP_200_OK,
        )


class StockReserveView(StockOperationView):
    operation = "reserve"


class StockReleaseView(StockOperationView):
    operation = "release"


class StockSellView(StockOperationView):
    operation = "sell"


class StockReceiveView(StockOperationView):
    operation = "receive"


class StockPlaceOrderView(StockOperationView):
    operation = "place_order"


class StockShipFromSupplierView(StockOperationView):
    operation = "ship_from_supplier"
