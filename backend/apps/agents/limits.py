# backend/apps/agents/limits.py

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from apps.transactions.models import Transaction
from .models import AgentProfile


class AgentLimitManager:
    """
    Gère les limites dynamiques des agents FubaPay.
    """

    BASE_DAILY_LIMIT = Decimal("200")       # Limite par défaut en USDC
    BASE_TRANSACTION_LIMIT = Decimal("100") # Limite max par transaction
    NEW_AGENT_LIMIT = Decimal("50")         # Nouveau agent limité
    HIGH_TRUST_MULTIPLIER = Decimal("3")    # Bonus pour agents fiables

    def __init__(self, agent):
        self.agent = agent
        self.profile = AgentProfile.objects.get(user=agent)

    # ---------------------------
    # CALCUL LIMITE JOURNALIÈRE
    # ---------------------------
    def get_daily_limit(self):
        """
        Retourne la limite journalière dynamique
        selon le score IA.
        """

        score = self.profile.reputation_score

        if score < 40:
            return self.NEW_AGENT_LIMIT

        if score >= 80:
            return self.BASE_DAILY_LIMIT * self.HIGH_TRUST_MULTIPLIER

        return self.BASE_DAILY_LIMIT

    # ---------------------------
    # LIMITE PAR TRANSACTION
    # ---------------------------
    def get_transaction_limit(self):
        score = self.profile.reputation_score

        if score >= 80:
            return self.BASE_TRANSACTION_LIMIT * Decimal("2")

        if score < 40:
            return Decimal("30")

        return self.BASE_TRANSACTION_LIMIT

    # ---------------------------
    # TOTAL UTILISÉ AUJOURD’HUI
    # ---------------------------
    def get_today_volume(self):
        today = timezone.now()
        start_day = today.replace(hour=0, minute=0, second=0, microsecond=0)

        total = (
            Transaction.objects
            .filter(agent=self.agent, created_at__gte=start_day, status="completed")
            .aggregate(Sum("amount"))["amount__sum"]
        )

        return total or Decimal("0")

    # ---------------------------
    # VÉRIFICATION TRANSACTION
    # ---------------------------
    def can_process(self, amount):
        """
        Vérifie si l’agent peut traiter une transaction.
        """

        amount = Decimal(amount)

        if self.profile.is_frozen:
            return False, "Compte agent gelé"

        if amount > self.get_transaction_limit():
            return False, "Montant dépasse la limite par transaction"

        today_total = self.get_today_volume()
        daily_limit = self.get_daily_limit()

        if today_total + amount > daily_limit:
            return False, "Limite journalière dépassée"

        return True, "Transaction autorisée"

    # ---------------------------
    # GEL AUTOMATIQUE
    # ---------------------------
    def auto_freeze_if_suspicious(self):
        """
        Gèle automatiquement si comportement suspect.
        """
        if self.profile.reputation_score < 20:
            self.profile.is_frozen = True
            self.profile.save()
            return True

        return False