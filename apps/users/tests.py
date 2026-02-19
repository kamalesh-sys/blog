from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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
