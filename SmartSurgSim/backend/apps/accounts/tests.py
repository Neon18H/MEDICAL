from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post('/api/auth/register', {
            'username': 'testuser',
            'password': 'Testpass123!'
        }, format='json')
        self.assertEqual(response.status_code, 201)

        login = self.client.post('/api/auth/login', {
            'username': 'testuser',
            'password': 'Testpass123!'
        }, format='json')
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data)
