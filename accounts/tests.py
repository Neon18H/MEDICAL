from rest_framework.test import APITestCase

from .models import User


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="Pass123!", role="STUDENT")

    def test_login_refresh(self):
        response = self.client.post("/api/auth/login/", {"username": "tester", "password": "Pass123!"}, format="json")
        self.assertEqual(response.status_code, 200)
        refresh = response.data["refresh"]
        refresh_response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(refresh_response.status_code, 200)
