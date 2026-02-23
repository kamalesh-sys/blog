from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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
