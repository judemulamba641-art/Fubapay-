# backend/apps/ai_engine/scoring.py

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.agents.models import AgentProfile
from apps.transactions.models import Transaction


class AIScoringEngine:
    """
    Moteur central de scoring comportemental FubaPay.
    Combine historique, stabilité, volume et risque.
    """

    BASE_SCORE = 50
    MAX_SCORE = 100
    MIN_SCORE = 0

    def __init__(self, agent):
        self.agent = agent
        self.profile = AgentProfile.objects.get(user=agent)

    # =====================================================
    # RECALCUL GLOBAL INTELLIGENT
    # =====================================================

    def calculate_score(self):
        """
        Recalcule complètement le score IA
        en fonction du comportement global.
        """

        transactions = Transaction.objects.filter(agent=self.agent)

        completed = transactions.filter(status="completed").count()
        failed = transactions.filter(status="failed").count()
        disputed = transactions.filter(status="disputed").count()

        total_volume = transactions.filter(
            status="completed"
        ).aggregate_sum()

        score = self.BASE_SCORE

        # ---------------------------------
        # POSITIF
        # ---------------------------------

        score += completed * 0.4
        score += min(20, completed * 0.1)  # plafond bonus volume activité

        # Bonus stabilité (30 derniers jours)
        score += self._stability_bonus()

        # ---------------------------------
        # NÉGATIF
        # ---------------------------------

        score -= failed * 2
        score -= disputed * 6
        score -= self._recent_failure_penalty()

        # Normalisation
        score = max(self.MIN_SCORE, min(self.MAX_SCORE, int(score)))

        self.profile.reputation_score = score
        self.profile.save()
        self.profile.update_trust_level()

        return score

    # =====================================================
    # BONUS STABILITÉ
    # =====================================================

    def _stability_bonus(self):
        """
        Bonus si aucune activité suspecte récente.
        """

        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        disputes_recent = Transaction.objects.filter(
            agent=self.agent,
            status="disputed",
            created_at__gte=last_30_days
        ).count()

        if disputes_recent == 0:
            return 10

        return 0

    # =====================================================
    # PÉNALITÉ ÉCHECS RÉCENTS
    # =====================================================

    def _recent_failure_penalty(self):

        now = timezone.now()
        last_7_days = now - timedelta(days=7)

        failures = Transaction.objects.filter(
            agent=self.agent,
            status="failed",
            created_at__gte=last_7_days
        ).count()

        if failures >= 5:
            return 10
        elif failures >= 3:
            return 5

        return 0

    # =====================================================
    # MISE À JOUR APRÈS TRANSACTION
    # =====================================================

    def update_after_transaction(self, transaction):
        """
        Mise à jour rapide après une transaction
        sans recalcul complet.
        """

        if transaction.status == "completed":
            self._increase(1)

        elif transaction.status == "failed":
            self._decrease(3)

        elif transaction.status == "disputed":
            self._decrease(7)

        self.profile.update_trust_level()

    # =====================================================
    # HELPERS
    # =====================================================

    def _increase(self, points):
        self.profile.reputation_score = min(
            self.MAX_SCORE,
            self.profile.reputation_score + points
        )
        self.profile.save()

    def _decrease(self, points):
        self.profile.reputation_score = max(
            self.MIN_SCORE,
            self.profile.reputation_score - points
        )
        self.profile.save()