from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.image_utils import upload_image_file
from .models import Follow
from .serializers import (
    UserLoginSerializer,
    UserPublicSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


User = get_user_model()


def get_user_or_404(user_id):
    user = User.objects.filter(id=user_id).first()
    if user is None:
        raise NotFound("User not found.")
    return user


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


class FollowToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        target_user = get_user_or_404(user_id)

        if request.user.id == target_user.id:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user,
        )
        if created:
            return Response(
                {"detail": "User followed.", "following": True},
                status=status.HTTP_201_CREATED,
            )

        follow.delete()
        return Response(
            {"detail": "User unfollowed.", "following": False},
            status=status.HTTP_200_OK,
        )


class UserFollowerListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_user_or_404(user_id)
        serializer = UserPublicSerializer(user.followers.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFollowingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_user_or_404(user_id)
        serializer = UserPublicSerializer(user.following.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
