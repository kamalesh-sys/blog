from django.db import transaction
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.email_notifications import send_activity_email
from apps.common.image_utils import upload_image_file
from .models import Follow
from .serializers import (
    FollowToggleResponseSerializer,
    ImageUploadRequestSerializer,
    ImageUploadResponseSerializer,
    TokenSerializer,
    UserLoginSerializer,
    UserPublicDetailSerializer,
    UserPublicSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserWithTokenSerializer,
)


User = get_user_model()


def get_user_or_404(user_id):
    user = User.objects.filter(id=user_id).first()
    if user is None:
        raise NotFound("User not found.")
    return user


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Creates a new user account and returns the user profile along with an auth token.",
        tags=["Auth"],
        request=UserRegistrationSerializer,
        responses={
            201: UserWithTokenSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        auth=[],
    )
)
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


@extend_schema_view(
    post=extend_schema(
        summary="Login user",
        description="Authenticates with username and password. Returns an auth token to include in subsequent requests as: `Authorization: Token <token>`.",
        tags=["Auth"],
        request=UserLoginSerializer,
        responses={
            200: TokenSerializer,
            400: OpenApiResponse(description="Invalid credentials or missing fields"),
        },
        auth=[],
    )
)
class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        if user.email:
            username_tag = f"@{user.username}"
            send_activity_email(
                subject="New login to your account",
                message=f"Your account, {username_tag}, was logged in.",
                recipient_list=[user.email],
            )

        response_data = {"token": token.key}
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Get current authenticated user",
        tags=["Users"],
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
    put=extend_schema(
        summary="Replace current user profile",
        tags=["Users"],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
    patch=extend_schema(
        summary="Partially update current user profile",
        tags=["Users"],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        summary="Get public profile by user id",
        tags=["Users"],
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="User id"),
        ],
        responses={
            200: UserPublicDetailSerializer,
            404: OpenApiResponse(description="User not found"),
        },
        auth=[],
    )
)
class UserPublicDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_user_or_404(user_id)
        serializer = UserPublicDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        summary="Upload an image",
        tags=["Uploads"],
        request=ImageUploadRequestSerializer,
        responses={
            201: ImageUploadResponseSerializer,
            400: OpenApiResponse(description="Invalid image upload request"),
            401: OpenApiResponse(description="Authentication required"),
        },
    )
)
class ImageUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image = request.FILES.get("file")
        image_url = upload_image_file(request, image)

        return Response(
            {"url": image_url},
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    post=extend_schema(
        summary="Follow or unfollow a user",
        description="Toggles the follow state for the target user. Returns 201 when the user is followed, 200 when unfollowed.",
        tags=["Follows"],
        request=None,
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="Target user id"),
        ],
        responses={
            200: FollowToggleResponseSerializer,
            201: FollowToggleResponseSerializer,
            400: OpenApiResponse(description="Cannot follow yourself"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="User not found"),
        },
    )
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
                {"detail": f"{request.user.username} followed {target_user.username}", "following": True},
                status=status.HTTP_201_CREATED,
            )

        follow.delete()
        return Response(
            {"detail": f"{request.user.username} unfollowed {target_user.username}", "following": False},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="List followers of a user",
        tags=["Follows"],
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="User id"),
        ],
        responses={
            200: UserPublicSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="User not found"),
        },
    )
)
class UserFollowerListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_user_or_404(user_id)
        serializer = UserPublicSerializer(user.followers.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List users followed by a user",
        tags=["Follows"],
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="User id"),
        ],
        responses={
            200: UserPublicSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="User not found"),
        },
    )
)
class UserFollowingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_user_or_404(user_id)
        serializer = UserPublicSerializer(user.following.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
