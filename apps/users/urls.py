from django.urls import path

from .views import (
    CurrentUserAPIView,
    FollowToggleAPIView,
    ImageUploadAPIView,
    UserFollowerListAPIView,
    UserFollowingListAPIView,
    UserLoginAPIView,
    UserRegistrationAPIView,
)

urlpatterns = [
    path("auth/register/", UserRegistrationAPIView.as_view(), name="user-register"),
    path("auth/login/", UserLoginAPIView.as_view(), name="user-login"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="current-user"),
    path("users/<int:user_id>/follow/", FollowToggleAPIView.as_view(), name="follow-toggle"),
    path("users/<int:user_id>/followers/", UserFollowerListAPIView.as_view(), name="user-follower-list"),
    path("users/<int:user_id>/following/", UserFollowingListAPIView.as_view(), name="user-following-list"),
    path("uploads/image/", ImageUploadAPIView.as_view(), name="image-upload"),
]
