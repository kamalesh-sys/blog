from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.image_utils import upload_image_file
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
