from django.urls import path

from .views import (
    PostCommentListCreateAPIView,
    PostLikeToggleAPIView,
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    UserLikedPostListAPIView,
    UserPostListAPIView,
)

urlpatterns = [
    path("posts/", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", PostRetrieveUpdateDestroyAPIView.as_view(), name="post-detail"),
    path("users/<int:user_id>/posts/", UserPostListAPIView.as_view(), name="user-post-list"),
    path(
        "users/<int:user_id>/liked-posts/",
        UserLikedPostListAPIView.as_view(),
        name="user-liked-post-list",
    ),
    path(
        "posts/<int:post_id>/comments/",
        PostCommentListCreateAPIView.as_view(),
        name="post-comment-list-create",
    ),
    path("posts/<int:post_id>/like/", PostLikeToggleAPIView.as_view(), name="post-like-toggle"),
]