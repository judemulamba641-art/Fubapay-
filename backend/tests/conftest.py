import os
import pytest
from rest_framework.test import APIClient
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

User = get_user_model()


# ==========================================================
# 🔌 Auto-load fixtures modules
# ==========================================================

pytest_plugins = [
    "tests.fixtures.users",
    "tests.fixtures.wallets",
    "tests.fixtures.transactions",
]


# ==========================================================
# 🌍 Global Test Environment Setup
# ==========================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """
    Configure secure test environment.
    """
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]
    os.environ["ENVIRONMENT"] = "test"
    yield


# ==========================================================
# 🧪 Base API Client
# ==========================================================

@pytest.fixture
def api_client():
    return APIClient()


# ==========================================================
# 🔐 Authenticated Client
# ==========================================================

@pytest.fixture
def authenticated_client(db):
    """
    Returns APIClient already authenticated with JWT.
    """
    user = User.objects.create_user(
        email="authuser@gmail.com",
        password="SecurePass123!"
    )

    refresh = RefreshToken.for_user(user)

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )

    return client


# ==========================================================
# 🔐 Custom Authenticated Client (dynamic user)
# ==========================================================

@pytest.fixture
def auth_client_factory(db):
    """
    Factory to create authenticated clients dynamically.
    Usage:
        client, user = auth_client_factory(email="x@gmail.com")
    """

    def create_client(email="factory@gmail.com", role="client"):
        user = User.objects.create_user(
            email=email,
            password="SecurePass123!",
            role=role
        )

        refresh = RefreshToken.for_user(user)

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        return client, user

    return create_client


# ==========================================================
# 📦 Mock IPFS (global safe default)
# ==========================================================

@pytest.fixture(autouse=True)
def mock_ipfs():
    """
    Automatically mock IPFS calls during tests.
    """
    with patch("apps.ipfs_storage.client.ipfs_add") as mock:
        mock.return_value = {"Hash": "QmMockedCID123456"}
        yield mock


# ==========================================================
# 🧠 Mock AI Risk Engine (optional)
# ==========================================================

@pytest.fixture
def mock_ai_approved():
    with patch("apps.ai_engine.fraud.evaluate_risk") as mock:
        mock.return_value = "approved"
        yield mock


@pytest.fixture
def mock_ai_blocked():
    with patch("apps.ai_engine.fraud.evaluate_risk") as mock:
        mock.return_value = "blocked"
        yield mock


# ==========================================================
# 🧹 Database Clean Reset (extra safety)
# ==========================================================

@pytest.fixture(autouse=True)
def reset_sequences(db):
    """
    Optional: ensures predictable ID increments if needed.
    """
    yield


# ==========================================================
# 📊 Test Metadata Helper
# ==========================================================

@pytest.fixture
def test_metadata():
    return {
        "app": "FubaPay",
        "environment": "test",
        "version": "startup-e2e-v1"
    }