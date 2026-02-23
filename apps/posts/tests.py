from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Post, PostLike, Tag
from apps.users.models import Follow


User = get_user_model()


class PostTagAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-pass-123",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_post_with_tags(self):
        payload = {
            "name": "Tagged post",
            "content": "Post body",
            "tag_names": ["  django ", "api", "Django"],
        }

        response = self.client.post(reverse("post-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data["tags"], ["django", "api"])
        self.assertEqual(Tag.objects.count(), 2)

    def test_patch_post_updates_tags(self):
        post = Post.objects.create(author=self.user, name="First", content="Body")
        post.tags.add(Tag.objects.create(name="django"), Tag.objects.create(name="rest"))

        payload = {"tag_names": ["python", "api"]}
        response = self.client.patch(
            reverse("post-detail", kwargs={"pk": post.id}), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data["tags"], ["python", "api"])
        self.assertCountEqual(
            list(post.tags.values_list("name", flat=True)),
            ["python", "api"],
        )

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_create_post_accepts_optional_file_and_sets_image_url(self):
        image = SimpleUploadedFile("post.jpg", b"fake-image-content", content_type="image/jpeg")
        payload = {
            "name": "Post with uploaded image",
            "content": "Body",
            "file": image,
        }

        response = self.client.post(
            reverse("post-list-create"),
            payload,
            format="multipart",
            HTTP_HOST="example.com",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/media/uploads/", response.data["image"])

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_patch_post_accepts_optional_file_and_updates_image_url(self):
        post = Post.objects.create(author=self.user, name="First", content="Body")
        image = SimpleUploadedFile("updated.jpg", b"fake-image-content", content_type="image/jpeg")

        response = self.client.patch(
            reverse("post-detail", kwargs={"pk": post.id}),
            {"file": image},
            format="multipart",
            HTTP_HOST="example.com",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("/media/uploads/", response.data["image"])


class PostErrorHandlingTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="strong-pass-123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="strong-pass-123",
        )
        self.post = Post.objects.create(author=self.owner, name="Hello", content="World")

    def test_create_post_requires_authentication(self):
        payload = {"name": "No auth", "content": "No auth body"}
        response = self.client.post(reverse("post-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)

    def test_non_owner_cannot_update_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            reverse("post-detail", kwargs={"pk": self.post.id}),
            {"name": "Hacked title"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["message"], "Only the owner can edit this post.")

    def test_post_not_found_returns_404(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": 99999}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Post not found.")

    def test_create_post_with_blank_name_returns_validation_error(self):
        self.client.force_authenticate(user=self.owner)
        payload = {"name": "   ", "content": "Body"}

        response = self.client.post(reverse("post-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Validation error.")
        self.assertIn("name", response.data["errors"])


class PostQueryFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="query-user",
            email="query@example.com",
            password="strong-pass-123",
        )
        self.other_user = User.objects.create_user(
            username="another-user",
            email="another@example.com",
            password="strong-pass-123",
        )

        self.python_tag = Tag.objects.create(name="python")
        self.django_tag = Tag.objects.create(name="django")

        self.post_1 = Post.objects.create(
            author=self.user,
            name="Django tips",
            content="Great content for backend",
            category="tech",
            image="https://example.com/p1.jpg",
        )
        self.post_1.tags.add(self.django_tag)

        self.post_2 = Post.objects.create(
            author=self.other_user,
            name="Python basics",
            content="Start python quickly",
            category="coding",
        )
        self.post_2.tags.add(self.python_tag)

        PostLike.objects.create(post=self.post_1, user=self.other_user)

    def test_post_search_supports_content_and_tags(self):
        response_by_content = self.client.get(reverse("post-list-create"), {"search": "backend"})
        response_by_tag = self.client.get(reverse("post-list-create"), {"search": "python"})

        self.assertEqual(response_by_content.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_by_content.data), 1)
        self.assertEqual(response_by_content.data[0]["id"], self.post_1.id)

        self.assertEqual(response_by_tag.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_by_tag.data), 1)
        self.assertEqual(response_by_tag.data[0]["id"], self.post_2.id)

    def test_post_list_can_filter_by_category(self):
        response = self.client.get(reverse("post-list-create"), {"category": "tech"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post_1.id)

    def test_liked_posts_are_retrievable_for_user(self):
        response = self.client.get(
            reverse("user-liked-post-list", kwargs={"user_id": self.other_user.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post_1.id)

    def test_following_posts_are_retrievable_for_user(self):
        Follow.objects.create(follower=self.other_user, following=self.user)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse("following-post-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post_1.id)
