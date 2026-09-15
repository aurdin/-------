from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.services import attach_guest_cart_to_customer

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

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
