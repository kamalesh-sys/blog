from django.urls import path

from .views import CurrentUserAPIView, ImageUploadAPIView, UserLoginAPIView, UserRegistrationAPIView

urlpatterns = [
    path("auth/register/", UserRegistrationAPIView.as_view(), name="user-register"),
    path("auth/login/", UserLoginAPIView.as_view(), name="user-login"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="current-user"),
    path("uploads/image/", ImageUploadAPIView.as_view(), name="image-upload"),
]