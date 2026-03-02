from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.image_utils import upload_image_file
from .models import Comment, Post, PostLike
from .serializers import (
    CommentSerializer,
    DetailResponseSerializer,
    PostLikeToggleResponseSerializer,
    PostSerializer,
)


User = get_user_model()


def get_post_with_author_and_tags_or_404(post_id):
    post = (
        Post.objects.select_related("author")
        .prefetch_related("tags")
        .filter(id=post_id)
        .first()
    )
    if post is None:
        raise NotFound("Post not found.")
    return post


@extend_schema_view(
    get=extend_schema(
        summary="List posts",
        tags=["Posts"],
        parameters=[
            OpenApiParameter("search", str, OpenApiParameter.QUERY, description="Search in content and tags"),
            OpenApiParameter("category", str, OpenApiParameter.QUERY, description="Filter by exact category"),
        ],
        responses={200: PostSerializer(many=True)},
        auth=[],
    ),
    post=extend_schema(
        summary="Create post",
        tags=["Posts"],
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
)
class PostListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = list(Post.objects.select_related("author").prefetch_related("tags").all())

        search_text = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()

        if search_text:
            lowered_search = search_text.lower()
            searched_posts = []
            for post in posts:
                content_text = (post.content or "").lower()
                tag_match = False
                for tag in post.tags.all():
                    if lowered_search in (tag.name or "").lower():
                        tag_match = True
                        break

                if lowered_search in content_text or tag_match:
                    searched_posts.append(post)
            posts = searched_posts

        if category:
            lowered_category = category.lower()
            category_filtered_posts = []
            for post in posts:
                if (post.category or "").lower() == lowered_category:
                    category_filtered_posts.append(post)
            posts = category_filtered_posts

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        payload = request.data.copy()
        payload.pop("file", None)
        image_file = request.FILES.get("file")
        if image_file is not None:
            payload["image"] = upload_image_file(request, image_file)

        serializer = PostSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve post by id",
        tags=["Posts"],
        responses={
            200: PostSerializer,
            404: OpenApiResponse(description="Post not found"),
        },
        auth=[],
    ),
    put=extend_schema(
        summary="Replace post",
        tags=["Posts"],
        request=PostSerializer,
        responses={
            200: PostSerializer,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Only the owner can edit this post"),
            404: OpenApiResponse(description="Post not found"),
        },
    ),
    patch=extend_schema(
        summary="Partially update post",
        tags=["Posts"],
        request=PostSerializer,
        responses={
            200: PostSerializer,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Only the owner can edit this post"),
            404: OpenApiResponse(description="Post not found"),
        },
    ),
    delete=extend_schema(
        summary="Delete post",
        tags=["Posts"],
        responses={
            200: DetailResponseSerializer,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Only the owner can delete this post"),
            404: OpenApiResponse(description="Post not found"),
        },
    ),
)
class PostRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)

        if post.author != request.user:
            raise PermissionDenied("Only the owner can edit this post.")

        payload = request.data.copy()
        payload.pop("file", None)
        image_file = request.FILES.get("file")
        if image_file is not None:
            payload["image"] = upload_image_file(request, image_file)

        serializer = PostSerializer(post, data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=post.author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)

        if post.author != request.user:
            raise PermissionDenied("Only the owner can edit this post.")

        payload = request.data.copy()
        payload.pop("file", None)
        image_file = request.FILES.get("file")
        if image_file is not None:
            payload["image"] = upload_image_file(request, image_file)

        serializer = PostSerializer(post, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=post.author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)

        if post.author == request.user:
            post.delete()
            return Response({"detail": "Post deleted."}, status=status.HTTP_200_OK)

        raise PermissionDenied("Only the owner can delete this post.")


@extend_schema_view(
    get=extend_schema(
        summary="List posts by user",
        tags=["Posts"],
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="User id"),
        ],
        responses={
            200: PostSerializer(many=True),
            404: OpenApiResponse(description="User not found"),
        },
        auth=[],
    )
)
class UserPostListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, user_id):
        if not User.objects.filter(id=user_id).exists():
            raise NotFound("User not found.")

        posts = (
            Post.objects.select_related("author")
            .prefetch_related("tags")
            .filter(author_id=user_id)
        )
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List posts liked by user",
        tags=["Posts"],
        parameters=[
            OpenApiParameter("user_id", int, OpenApiParameter.PATH, description="User id"),
        ],
        responses={
            200: PostSerializer(many=True),
            404: OpenApiResponse(description="User not found"),
        },
        auth=[],
    )
)
class UserLikedPostListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, user_id):
        if not User.objects.filter(id=user_id).exists():
            raise NotFound("User not found.")

        all_posts = Post.objects.select_related("author").prefetch_related("tags", "likes").all()
        posts = []
        for post in all_posts:
            is_liked_by_user = False
            for like in post.likes.all():
                if like.user_id == user_id:
                    is_liked_by_user = True
                    break

            if is_liked_by_user:
                posts.append(post)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List posts from followed users",
        description="Returns all posts authored by users that the authenticated user is following, ordered by recency.",
        tags=["Posts"],
        responses={
            200: PostSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
    )
)
class FollowingPostListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        following_users = list(request.user.following.all())
        all_posts = Post.objects.select_related("author").prefetch_related("tags").all()

        posts = []
        for post in all_posts:
            if post.author in following_users:
                posts.append(post)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List comments for a post",
        tags=["Comments"],
        parameters=[
            OpenApiParameter("post_id", int, OpenApiParameter.PATH, description="Post id"),
        ],
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiResponse(description="Post not found"),
        },
        auth=[],
    ),
    post=extend_schema(
        summary="Create comment for a post",
        tags=["Comments"],
        parameters=[
            OpenApiParameter("post_id", int, OpenApiParameter.PATH, description="Post id"),
        ],
        request=CommentSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found"),
        },
    ),
)
class PostCommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, post_id):
        post = get_post_with_author_and_tags_or_404(post_id)
        comments = Comment.objects.select_related("author", "post").filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_id):
        post = get_post_with_author_and_tags_or_404(post_id)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        summary="Like or unlike a post",
        description="Toggles the like state for the authenticated user. Returns 201 when the post is liked, 200 when it is unliked.",
        tags=["Posts"],
        request=None,
        parameters=[
            OpenApiParameter("post_id", int, OpenApiParameter.PATH, description="Post id"),
        ],
        responses={
            200: PostLikeToggleResponseSerializer,
            201: PostLikeToggleResponseSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found"),
        },
    )
)
class PostLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_post_with_author_and_tags_or_404(post_id)
        like_data = PostLike.objects.get_or_create(post=post, user=request.user)
        like = like_data[0]
        created = like_data[1]

        if created:
            response_data = {"detail": "Post liked.", "liked": True}
            return Response(response_data, status=status.HTTP_201_CREATED)

        like.delete()
        response_data = {"detail": "Post unliked.", "liked": False}
        return Response(response_data, status=status.HTTP_200_OK)
