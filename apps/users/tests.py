from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Follow


User = get_user_model()


class UserAuthErrorHandlingTests(APITestCase):
    def test_register_short_password_returns_standard_400_error(self):
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "123",
        }

        response = self.client.post(reverse("user-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Validation error.")
        self.assertIn("password", response.data["errors"])

    def test_login_missing_fields_returns_standard_400_error(self):
        response = self.client.post(reverse("user-login"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Validation error.")
        self.assertIn("username", response.data["errors"])
        self.assertIn("password", response.data["errors"])

    def test_current_user_requires_authentication(self):
        response = self.client.get(reverse("current-user"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status_code"], status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)


class UserProfileFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-pass-123",
        )

    def test_register_returns_both_username_and_email_errors_when_both_exist(self):
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "strong-pass-123",
        }

        response = self.client.post(reverse("user-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data["errors"])
        self.assertIn("email", response.data["errors"])

    def test_current_user_profile_can_be_updated(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "phone_no": "9999999999",
            "profile_pic": "https://example.com/avatar.jpg",
            "dob": "1998-01-10",
        }

        response = self.client.patch(reverse("current-user"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_no"], payload["phone_no"])
        self.assertEqual(response.data["profile_pic"], payload["profile_pic"])
        self.assertEqual(response.data["dob"], payload["dob"])

    def test_register_rejects_invalid_phone_number(self):
        payload = {
            "username": "bob",
            "email": "bob@example.com",
            "password": "strong-pass-123",
            "phone_no": "12345",
        }

        response = self.client.post(reverse("user-register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_no", response.data["errors"])

    def test_current_user_profile_rejects_invalid_phone_number(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("current-user"),
            {"phone_no": "12-34"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_no", response.data["errors"])

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_current_user_profile_can_upload_profile_pic_via_file_field(self):
        self.client.force_authenticate(user=self.user)
        image = SimpleUploadedFile("avatar.jpg", b"fake-image-content", content_type="image/jpeg")

        response = self.client.patch(
            reverse("current-user"),
            {"file": image},
            format="multipart",
            HTTP_HOST="example.com",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("/media/uploads/", response.data["profile_pic"])

    def test_user_public_detail_is_accessible_without_auth(self):
        response = self.client.get(
            reverse("user-public-detail", kwargs={"user_id": self.user.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertIn("followers_count", response.data)
        self.assertIn("following_count", response.data)
        self.assertNotIn("email", response.data)
        self.assertNotIn("phone_no", response.data)

    def test_user_public_detail_returns_not_found_for_invalid_user(self):
        response = self.client.get(
            reverse("user-public-detail", kwargs={"user_id": 999999})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserFollowFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice-follow",
            email="alice-follow@example.com",
            password="strong-pass-123",
        )
        self.target = User.objects.create_user(
            username="bob-follow",
            email="bob-follow@example.com",
            password="strong-pass-123",
        )
        self.other = User.objects.create_user(
            username="charlie-follow",
            email="charlie-follow@example.com",
            password="strong-pass-123",
        )
        self.client.force_authenticate(user=self.user)

    def test_follow_toggle_and_follower_following_lists(self):
        follow_response = self.client.post(reverse("follow-toggle", kwargs={"user_id": self.target.id}))
        self.assertEqual(follow_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(follow_response.data["following"])

        following_response = self.client.get(
            reverse("user-following-list", kwargs={"user_id": self.user.id})
        )
        self.assertEqual(following_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(following_response.data), 1)
        self.assertEqual(following_response.data[0]["id"], self.target.id)

        followers_response = self.client.get(
            reverse("user-follower-list", kwargs={"user_id": self.target.id})
        )
        self.assertEqual(followers_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(followers_response.data), 1)
        self.assertEqual(followers_response.data[0]["id"], self.user.id)

        unfollow_response = self.client.post(reverse("follow-toggle", kwargs={"user_id": self.target.id}))
        self.assertEqual(unfollow_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unfollow_response.data["following"])

    def test_user_cannot_follow_self(self):
        response = self.client.post(reverse("follow-toggle", kwargs={"user_id": self.user.id}))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "You cannot follow yourself.")

    def test_follow_model_rejects_self_follow(self):
        with self.assertRaises(ValidationError):
            Follow.objects.create(follower=self.user, following=self.user)

    def test_follow_model_rejects_duplicate_follow(self):
        Follow.objects.create(follower=self.user, following=self.target)
        with self.assertRaises(ValidationError):
            Follow.objects.create(follower=self.user, following=self.target)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@test.local",
)
class UserEmailNotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="email-user",
            email="email-user@example.com",
            password="strong-pass-123",
        )
        self.target = User.objects.create_user(
            username="email-target",
            email="email-target@example.com",
            password="strong-pass-123",
        )

    def test_follow_sends_email_to_followed_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("follow-toggle", kwargs={"user_id": self.target.id})
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.target.email])
        self.assertIn("started following you", mail.outbox[0].subject)
        self.assertIn(self.user.username, mail.outbox[0].body)

    def test_login_sends_email_to_same_user(self):
        mail.outbox = []

        response = self.client.post(
            reverse("user-login"),
            {"username": self.user.username, "password": "strong-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("New login to your account", mail.outbox[0].subject)
        self.assertIn(self.user.username, mail.outbox[0].body)

    def test_profile_pic_update_sends_email_only_to_user_even_with_followers(self):
        follower = User.objects.create_user(
            username="follower-user",
            email="follower-user@example.com",
            password="strong-pass-123",
        )
        Follow.objects.create(follower=follower, following=self.user)
        mail.outbox = []

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("current-user"),
            {"profile_pic": "https://example.com/new-profile.jpg"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertNotIn(follower.email, mail.outbox[0].to)
        self.assertIn("updated profile picture", mail.outbox[0].subject)
        self.assertIn(self.user.username, mail.outbox[0].body)

    def test_profile_pic_update_sends_email_to_user_when_no_followers(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("current-user"),
            {"profile_pic": "https://example.com/self-only-profile.jpg"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("updated profile picture", mail.outbox[0].subject)
        self.assertIn(self.user.username, mail.outbox[0].body)
