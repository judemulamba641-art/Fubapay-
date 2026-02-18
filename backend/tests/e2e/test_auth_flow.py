import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthFlow:

    def setup_method(self):
        self.client = APIClient()
        self.register_url = "/api/accounts/register/"
        self.login_url = "/api/accounts/login/"
        self.protected_url = "/api/accounts/me/"

    # ✅ Test inscription Gmail
    def test_register_user_success(self):
        response = self.client.post(self.register_url, {
            "email": "startup@gmail.com",
            "role": "client"
        })

        assert response.status_code == 201
        assert User.objects.filter(email="startup@gmail.com").exists()

    # ❌ Email dupliqué
    def test_register_duplicate_email(self):
        User.objects.create_user(email="duplicate@gmail.com")

        response = self.client.post(self.register_url, {
            "email": "duplicate@gmail.com",
            "role": "client"
        })

        assert response.status_code in [400, 409]

    # ✅ Login utilisateur
    def test_login_success(self):
        user = User.objects.create_user(
            email="login@gmail.com",
            password="StrongPass123!"
        )

        response = self.client.post(self.login_url, {
            "email": "login@gmail.com",
            "password": "StrongPass123!"
        })

        assert response.status_code == 200
        assert "access" in response.data

    # ❌ Mauvais mot de passe
    def test_login_wrong_password(self):
        User.objects.create_user(
            email="wrongpass@gmail.com",
            password="CorrectPass123!"
        )

        response = self.client.post(self.login_url, {
            "email": "wrongpass@gmail.com",
            "password": "BadPassword"
        })

        assert response.status_code == 401

    # 🔐 Endpoint protégé sans token
    def test_protected_endpoint_without_token(self):
        response = self.client.get(self.protected_url)
        assert response.status_code in [401, 403]

    # 🔐 Endpoint protégé avec token
    def test_protected_endpoint_with_token(self):
        user = User.objects.create_user(
            email="secure@gmail.com",
            password="SecurePass123!"
        )

        login = self.client.post(self.login_url, {
            "email": "secure@gmail.com",
            "password": "SecurePass123!"
        })

        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(self.protected_url)

        assert response.status_code == 200
        assert response.data["email"] == "secure@gmail.com"