import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet

User = get_user_model()


@pytest.mark.django_db
class TestWalletFlow:

    def setup_method(self):
        self.client = APIClient()
        self.create_wallet_url = "/api/wallets/create/"
        self.wallet_detail_url = "/api/wallets/me/"

    def authenticate(self, email):
        user = User.objects.create_user(
            email=email,
            password="WalletPass123!"
        )
        login = self.client.post("/api/accounts/login/", {
            "email": email,
            "password": "WalletPass123!"
        })
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return user

    # ✅ Création wallet
    def test_create_wallet_success(self):
        self.authenticate("walletuser@gmail.com")

        response = self.client.post(self.create_wallet_url)

        assert response.status_code == 201
        assert Wallet.objects.count() == 1
        assert response.data["balance"] == 0

    # ❌ Double wallet interdit
    def test_create_wallet_twice(self):
        self.authenticate("doublewallet@gmail.com")

        self.client.post(self.create_wallet_url)
        response = self.client.post(self.create_wallet_url)

        assert response.status_code in [400, 409]

    # 🔐 Accès wallet protégé
    def test_wallet_requires_auth(self):
        response = self.client.get(self.wallet_detail_url)
        assert response.status_code in [401, 403]

    # 🔐 Wallet appartient au bon user
    def test_wallet_access_isolated_between_users(self):
        # User 1
        self.authenticate("user1@gmail.com")
        self.client.post(self.create_wallet_url)

        # Switch user
        self.client = APIClient()
        self.authenticate("user2@gmail.com")

        response = self.client.get(self.wallet_detail_url)

        # User2 ne doit pas voir wallet user1
        assert response.status_code in [404, 403]

    # 🧪 Test transaction mock interne
    def test_wallet_balance_update(self):
        user = self.authenticate("balance@gmail.com")
        self.client.post(self.create_wallet_url)

        wallet = Wallet.objects.get(user=user)
        wallet.balance = 100
        wallet.save()

        response = self.client.get(self.wallet_detail_url)

        assert response.status_code == 200
        assert response.data["balance"] == 100