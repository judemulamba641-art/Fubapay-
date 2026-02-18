# backend/apps/agents/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class AgentProfile(models.Model):
    """
    Profil agent FubaPay.
    Chaque agent est lié à un utilisateur (auth Gmail).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_profile"
    )

    # ---------------------------
    # IDENTITÉ & STATUT
    # ---------------------------
    is_active = models.BooleanField(default=True)
    is_frozen = models.BooleanField(default=False)

    # ---------------------------
    # SCORING IA
    # ---------------------------
    reputation_score = models.IntegerField(default=50)
    trust_level = models.CharField(
        max_length=20,
        choices=[
            ("new", "New Agent"),
            ("standard", "Standard"),
            ("trusted", "Trusted"),
            ("elite", "Elite"),
        ],
        default="new"
    )

    # ---------------------------
    # LIMITES PERSONNALISÉES
    # ---------------------------
    custom_daily_limit = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True
    )

    custom_transaction_limit = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ---------------------------
    # STATISTIQUES
    # ---------------------------
    total_volume = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0")
    )

    total_transactions = models.IntegerField(default=0)

    successful_transactions = models.IntegerField(default=0)
    failed_transactions = models.IntegerField(default=0)

    dispute_count = models.IntegerField(default=0)

    # ---------------------------
    # MÉTADONNÉES
    # ---------------------------
    ip_address_last = models.GenericIPAddressField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------------------
    # MÉTHODES LOGIQUES
    # ---------------------------
    def update_trust_level(self):
        """
        Met à jour automatiquement le niveau de confiance
        selon le score IA.
        """

        if self.reputation_score >= 85:
            self.trust_level = "elite"
        elif self.reputation_score >= 70:
            self.trust_level = "trusted"
        elif self.reputation_score >= 50:
            self.trust_level = "standard"
        else:
            self.trust_level = "new"

        self.save()

    def increase_score(self, points=1):
        self.reputation_score = min(100, self.reputation_score + points)
        self.update_trust_level()

    def decrease_score(self, points=5):
        self.reputation_score = max(0, self.reputation_score - points)
        self.update_trust_level()

    def freeze(self):
        self.is_frozen = True
        self.save()

    def unfreeze(self):
        self.is_frozen = False
        self.save()

    def success_rate(self):
        if self.total_transactions == 0:
            return 0
        return (self.successful_transactions / self.total_transactions) * 100

    def __str__(self):
        return f"AgentProfile({self.user.email})"