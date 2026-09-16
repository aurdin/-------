from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.services import attach_guest_cart_to_customer

from .models import CustomerAddress, CustomerProfile
from .serializers import (
    CustomerAddressSerializer,
    CustomerProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012

    def post(self, request):
        # Запоминаем гостевую сессию ДО создания пользователя
        # и последующего login().
        guest_session_key = request.session.session_key

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Создаём профиль клиента.
        CustomerProfile.objects.create(
            user=user,
        )

        # Переносим или объединяем гостевую корзину
        # с персональной корзиной нового пользователя.
        attach_guest_cart_to_customer(
            guest_session_key,
            user,
        )

        # После успешной регистрации автоматически
        # авторизуем нового пользователя.
        login(request, user)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Необходимо указать username и password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Неверное имя пользователя или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Запоминаем гостевую сессию ДО login().
        #
        # Django login() меняет session key,
        # поэтому гостевую корзину нужно обработать
        # до смены сессии.
        guest_session_key = request.session.session_key

        attach_guest_cart_to_customer(
            guest_session_key,
            user,
        )

        login(request, user)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def post(self, request):
        logout(request)

        return Response(
            {"detail": "Выход выполнен успешно."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        profile = CustomerProfile.objects.get(
            user=request.user,
        )

        return Response(
            CustomerProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        profile = CustomerProfile.objects.get(
            user=request.user,
        )

        serializer = CustomerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class CustomerAddressListView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request):
        addresses = CustomerAddress.objects.filter(
            user=request.user,
        ).order_by(
            "-is_default",
            "-created_at",
        )

        serializer = CustomerAddressSerializer(
            addresses,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request):
        serializer = CustomerAddressSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("is_default", False):
            CustomerAddress.objects.filter(
                user=request.user,
                is_default=True,
            ).update(
                is_default=False,
            )

        address = serializer.save(
            user=request.user,
        )

        return Response(
            CustomerAddressSerializer(address).data,
            status=status.HTTP_201_CREATED,
        )
# ----------------------
class CustomerAddressDetailView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_object(self, request, pk):
        try:
            return CustomerAddress.objects.get(
                pk=pk,
                user=request.user,
            )
        except CustomerAddress.DoesNotExist:
            return None

    def get(self, request, pk):
        address = self.get_object(request, pk)

        if address is None:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CustomerAddressSerializer(address).data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request, pk):
        address = self.get_object(request, pk)

        if address is None:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerAddressSerializer(
            address,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("is_default", False):
            CustomerAddress.objects.filter(
                user=request.user,
                is_default=True,
            ).exclude(
                pk=address.pk,
            ).update(
                is_default=False,
            )

        serializer.save()

        return Response(
            CustomerAddressSerializer(address).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        address = self.get_object(request, pk)

        if address is None:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        address.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
