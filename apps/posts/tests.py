from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Post, Tag


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
