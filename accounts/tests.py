from django.urls import reverse
from rest_framework.test import APITestCase

from .models import User


class AuthTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            reverse("register"),
            {"username": "testuser", "email": "test@example.com", "password": "StrongPass123!", "role": "STUDENT"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)
