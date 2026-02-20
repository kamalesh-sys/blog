from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, Post, PostLike
from .serializers import CommentSerializer, PostSerializer


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


class PostListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = Post.objects.select_related("author").prefetch_related("tags").all()

        search_text = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()

        if search_text:
            posts = posts.filter(
                Q(content__icontains=search_text) | Q(tags__name__icontains=search_text)
            )

        if category:
            posts = posts.filter(category__iexact=category)

        posts = posts.distinct()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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

        serializer = PostSerializer(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=post.author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)

        if post.author != request.user:
            raise PermissionDenied("Only the owner can edit this post.")

        serializer = PostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=post.author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        post = get_post_with_author_and_tags_or_404(pk)

        if post.author == request.user:
            post.delete()
            return Response({"detail": "Post deleted."}, status=status.HTTP_200_OK)

        raise PermissionDenied("Only the owner can delete this post.")


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


class UserLikedPostListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, user_id):
        if not User.objects.filter(id=user_id).exists():
            raise NotFound("User not found.")

        posts = (
            Post.objects.select_related("author")
            .prefetch_related("tags")
            .filter(likes__user_id=user_id)
            .distinct()
        )
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
