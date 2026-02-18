import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet
from apps.transactions.models import Transaction

User = get_user_model()


@pytest.mark.django_db
class TestTransactionFlow:

    def setup_method(self):
        self.client = APIClient()
        self.transaction_url = "/api/transactions/pay/"
        self.login_url = "/api/accounts/login/"

    def authenticate(self, email):
        user = User.objects.create_user(
            email=email,
            password="TxPass123!"
        )
        wallet = Wallet.objects.create(user=user, balance=100)

        login = self.client.post(self.login_url, {
            "email": email,
            "password": "TxPass123!"
        })

        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        return user, wallet

    # ✅ Paiement valide
    def test_successful_transaction(self):
        user, wallet = self.authenticate("payer@gmail.com")

        response = self.client.post(self.transaction_url, {
            "amount": 10,
            "currency": "USDC",
            "recipient": "receiver_wallet_address"
        })

        assert response.status_code == 200
        assert response.data["status"] in ["approved", "limited"]

        wallet.refresh_from_db()
        assert wallet.balance == 90

        assert Transaction.objects.count() == 1
        assert "ipfs_hash" in response.data

    # ❌ Solde insuffisant
    def test_transaction_insufficient_balance(self):
        user, wallet = self.authenticate("lowbalance@gmail.com")
        wallet.balance = 5
        wallet.save()

        response = self.client.post(self.transaction_url, {
            "amount": 20,
            "currency": "USDC",
            "recipient": "receiver_wallet_address"
        })

        assert response.status_code == 400
        assert Transaction.objects.count() == 0

    # 🔐 Isolation entre utilisateurs
    def test_user_cannot_spend_other_wallet(self):
        user1, wallet1 = self.authenticate("user1@gmail.com")

        self.client = APIClient()
        user2, wallet2 = self.authenticate("user2@gmail.com")

        response = self.client.post(self.transaction_url, {
            "amount": 50,
            "currency": "USDC",
            "wallet_id": wallet1.id
        })

        assert response.status_code in [403, 404]

    # 🧪 Transaction marquée suspecte par IA
    def test_high_amount_triggers_ai_limit(self):
        user, wallet = self.authenticate("bigamount@gmail.com")

        response = self.client.post(self.transaction_url, {
            "amount": 10000,
            "currency": "USDC",
            "recipient": "receiver_wallet_address"
        })

        assert response.status_code in [200, 403]
        assert response.data["status"] in ["limited", "blocked"]