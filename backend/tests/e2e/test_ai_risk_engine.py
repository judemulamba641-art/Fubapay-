import pytest
from django.contrib.auth import get_user_model
from apps.ai_engine.fraud import evaluate_risk
from apps.wallets.models import Wallet
from apps.transactions.models import Transaction

User = get_user_model()


@pytest.mark.django_db
class TestAIRiskEngine:

    def create_user_with_history(self, email, tx_count=0, amount=10):
        user = User.objects.create_user(
            email=email,
            password="AiPass123!"
        )
        wallet = Wallet.objects.create(user=user, balance=10000)

        for _ in range(tx_count):
            Transaction.objects.create(
                user=user,
                amount=amount,
                currency="USDC",
                status="approved"
            )

        return user, wallet

    # ✅ Score normal
    def test_low_risk_transaction(self):
        user, wallet = self.create_user_with_history(
            "normal@gmail.com",
            tx_count=5,
            amount=20
        )

        decision = evaluate_risk(user=user, amount=25)

        assert decision in ["approved", "low_risk"]

    # ⚠️ Transaction suspecte
    def test_suspicious_amount(self):
        user, wallet = self.create_user_with_history(
            "suspicious@gmail.com",
            tx_count=2,
            amount=10
        )

        decision = evaluate_risk(user=user, amount=5000)

        assert decision in ["limited", "review"]

    # 🚨 Blocage comportement anormal
    def test_fraud_pattern_detection(self):
        user, wallet = self.create_user_with_history(
            "fraud@gmail.com",
            tx_count=50,
            amount=100
        )

        # Montant anormalement élevé
        decision = evaluate_risk(user=user, amount=50000)

        assert decision in ["blocked", "high_risk"]

    # 🔄 Test score dynamique
    def test_risk_score_increases_after_multiple_large_transactions(self):
        user, wallet = self.create_user_with_history(
            "dynamic@gmail.com",
            tx_count=3,
            amount=50
        )

        evaluate_risk(user=user, amount=1000)
        evaluate_risk(user=user, amount=2000)
        decision = evaluate_risk(user=user, amount=3000)

        assert decision in ["limited", "blocked", "review"]