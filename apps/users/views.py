from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.image_utils import upload_image_file
from .serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer


class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

        user_data = UserSerializer(user).data
        user_data["token"] = token.key

        return Response(user_data, status=status.HTTP_201_CREATED)


class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        response_data = {"token": token.key}
        return Response(response_data, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        payload = request.data.copy()
        payload.pop("file", None)
        image_file = request.FILES.get("file")
        if image_file is not None:
            payload["profile_pic"] = upload_image_file(request, image_file)

        serializer = UserSerializer(request.user, data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        payload = request.data.copy()
        payload.pop("file", None)
        image_file = request.FILES.get("file")
        if image_file is not None:
            payload["profile_pic"] = upload_image_file(request, image_file)

        serializer = UserSerializer(request.user, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image = request.FILES.get("file")
        image_url = upload_image_file(request, image)

        return Response(
            {"url": image_url},
            status=status.HTTP_201_CREATED
        )
