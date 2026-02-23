import os
from django.db import transaction
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
        serializer = UserSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 1. Get file
        image = request.FILES.get("file")

        if image is None:
            return Response(
                {"detail": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check content type
        if image.content_type is None:
            return Response(
                {"detail": "Invalid file"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not image.content_type.startswith("image/"):
            return Response(
                {"detail": "Only image files allowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Check size (5MB)
        if image.size > 5 * 1024 * 1024:
            return Response(
                {"detail": "Image must be under 5MB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Get extension
        name = image.name
        ext = os.path.splitext(name)[1].lower()

        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            ext = ".jpg"

        # 5. Create filename
        random_name = get_random_string(18)
        file_name = random_name + ext

        # 6. Save file
        path = "uploads/" + file_name
        saved_path = default_storage.save(path, image)

        image_url = request.build_absolute_uri(
            settings.MEDIA_URL + saved_path
        )

        # 7. Delete old image if exists
        old_image = request.user.profile_pic

        if old_image:
            if settings.MEDIA_URL in old_image:
                old_path = old_image.split(settings.MEDIA_URL)[-1]

                if default_storage.exists(old_path):
                    default_storage.delete(old_path)

        # 8. Update user
        request.user.profile_pic = image_url
        request.user.save()

        return Response(
            {"url": image_url},
            status=status.HTTP_201_CREATED
        )