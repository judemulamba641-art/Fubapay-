# backend/apps/ai_engine/fraud.py

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.agents.models import AgentProfile
from apps.transactions.models import Transaction


class FraudDetectionEngine:
    """
    Moteur antifraude basé sur règles déterministes.
    Rapide, local, sans appel API externe.
    """

    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40

    def __init__(self, agent):
        self.agent = agent
        self.profile = AgentProfile.objects.get(user=agent)

    # ==================================================
    # ANALYSE GLOBALE
    # ==================================================

    def analyze_transaction(self, transaction):
        """
        Retourne :
        {
            decision: APPROVE | REVIEW | BLOCK,
            risk_score: 0-100,
            flags: []
        }
        """

        risk_score = 0
        flags = []

        # 1️⃣ Agent gelé
        if self.profile.is_frozen:
            return {
                "decision": "BLOCK",
                "risk_score": 100,
                "flags": ["agent_frozen"]
            }

        # 2️⃣ Score trop bas
        if self.profile.reputation_score < 20:
            risk_score += 40
            flags.append("low_reputation")

        # 3️⃣ Montant anormalement élevé
        if Decimal(transaction.amount) > Decimal("1000"):
            risk_score += 25
            flags.append("high_amount")

        # 4️⃣ Pic de volume sur 24h
        volume_24h = self._get_volume_last_24h()
        if volume_24h > Decimal("2000"):
            risk_score += 20
            flags.append("volume_spike")

        # 5️⃣ Trop d’échecs récents
        failed_recent = self._failed_last_24h()
        if failed_recent >= 5:
            risk_score += 25
            flags.append("too_many_failures")

        # 6️⃣ Trop de litiges
        if self.profile.dispute_count >= 3:
            risk_score += 30
            flags.append("multiple_disputes")

        # ==================================================
        # DÉCISION
        # ==================================================

        if risk_score >= self.HIGH_RISK_THRESHOLD:
            decision = "BLOCK"
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return {
            "decision": decision,
            "risk_score": min(risk_score, 100),
            "flags": flags
        }

    # ==================================================
    # HELPERS
    # ==================================================

    def _get_volume_last_24h(self):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        transactions = Transaction.objects.filter(
            agent=self.agent,
            status="completed",
            created_at__gte=last_24h
        )

        total = sum(t.amount for t in transactions)

        return total or Decimal("0")

    def _failed_last_24h(self):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        return Transaction.objects.filter(
            agent=self.agent,
            status="failed",
            created_at__gte=last_24h
        ).count()