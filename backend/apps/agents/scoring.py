# backend/apps/agents/scoring.py

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.transactions.models import Transaction
from .models import AgentProfile


class AgentScoringEngine:
    """
    Moteur de scoring intelligent FubaPay.
    Ajuste le reputation_score selon le comportement.
    """

    MAX_SCORE = 100
    MIN_SCORE = 0

    def __init__(self, agent):
        self.agent = agent
        self.profile = AgentProfile.objects.get(user=agent)

    # -----------------------------
    # MISE À JOUR APRÈS TRANSACTION
    # -----------------------------
    def update_after_transaction(self, transaction):
        """
        Met à jour le score après une transaction.
        """

        if transaction.status == "completed":
            self._reward_success(transaction.amount)
        elif transaction.status == "failed":
            self._penalize_failure()
        elif transaction.status == "disputed":
            self._penalize_dispute()

        self.profile.update_trust_level()

    # -----------------------------
    # BONUS POUR BON COMPORTEMENT
    # -----------------------------
    def _reward_success(self, amount):

        # Bonus de base
        self._increase_score(1)

        # Bonus si volume important
        if Decimal(amount) > Decimal("200"):
            self._increase_score(2)

        # Bonus si aucune dispute récente
        if self.profile.dispute_count == 0:
            self._increase_score(1)

    # -----------------------------
    # PÉNALITÉS
    # -----------------------------
    def _penalize_failure(self):
        self._decrease_score(3)

    def _penalize_dispute(self):
        self.profile.dispute_count += 1
        self.profile.save()
        self._decrease_score(7)

    # -----------------------------
    # ANALYSE COMPORTEMENT JOURNALIER
    # -----------------------------
    def daily_behavior_check(self):
        """
        Vérifie comportement suspect sur 24h.
        """

        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        transactions = Transaction.objects.filter(
            agent=self.agent,
            created_at__gte=last_24h
        )

        total_volume = sum(t.amount for t in transactions if t.status == "completed")
        failed_count = transactions.filter(status="failed").count()

        # Volume anormalement élevé
        if total_volume > Decimal("1000"):
            self._decrease_score(5)

        # Trop d'échecs
        if failed_count >= 5:
            self._decrease_score(5)

    # -----------------------------
    # SCORE HELPERS
    # -----------------------------
    def _increase_score(self, points):
        self.profile.reputation_score = min(
            self.MAX_SCORE,
            self.profile.reputation_score + points
        )
        self.profile.save()

    def _decrease_score(self, points):
        self.profile.reputation_score = max(
            self.MIN_SCORE,
            self.profile.reputation_score - points
        )
        self.profile.save()

    # -----------------------------
    # SCORE GLOBAL RECALCUL
    # -----------------------------
    def full_recalculate(self):
        """
        Recalcule le score basé sur historique global.
        Utile pour audit ou recalibrage IA.
        """

        transactions = Transaction.objects.filter(agent=self.agent)

        completed = transactions.filter(status="completed").count()
        failed = transactions.filter(status="failed").count()
        disputed = transactions.filter(status="disputed").count()

        score = 50  # Base neutre

        score += completed * 0.5
        score -= failed * 2
        score -= disputed * 5

        score = max(self.MIN_SCORE, min(self.MAX_SCORE, int(score)))

        self.profile.reputation_score = score
        self.profile.save()
        self.profile.update_trust_level()

        return score