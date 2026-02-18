from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from .models import Transaction, RiskLevel


# -----------------------------------------
# CONFIGURATION
# -----------------------------------------

MAX_DAILY_VOLUME = Decimal("2000")
MAX_SINGLE_TX = Decimal("1000")
NEW_ACCOUNT_DAYS = 7
SUSPICIOUS_TX_COUNT_1H = 5


# -----------------------------------------
# CORE RISK ENGINE
# -----------------------------------------

class RiskEngine:

    def __init__(self, transaction: Transaction):
        self.transaction = transaction
        self.score = 0
        self.reasons = []

    # ------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------

    def evaluate(self):
        self.check_large_amount()
        self.check_daily_volume()
        self.check_new_account()
        self.check_frequency_spike()
        self.check_agent_risk()

        level = self.calculate_level()

        return {
            "risk_score": self.score,
            "risk_level": level,
            "reasons": self.reasons
        }

    # ------------------------------
    # RISK RULES
    # ------------------------------

    def check_large_amount(self):
        if self.transaction.amount >= MAX_SINGLE_TX:
            self.score += 30
            self.reasons.append("Large transaction amount")

    def check_daily_volume(self):
        today = timezone.now().date()

        daily_volume = Transaction.objects.filter(
            sender=self.transaction.sender,
            created_at__date=today,
            status__in=["CONFIRMED", "PROCESSING"]
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        if daily_volume + self.transaction.amount > MAX_DAILY_VOLUME:
            self.score += 25
            self.reasons.append("Exceeded daily transaction volume")

    def check_new_account(self):
        account_age = timezone.now() - self.transaction.sender.date_joined
        if account_age.days < NEW_ACCOUNT_DAYS:
            self.score += 15
            self.reasons.append("New account risk")

    def check_frequency_spike(self):
        one_hour_ago = timezone.now() - timedelta(hours=1)

        tx_count = Transaction.objects.filter(
            sender=self.transaction.sender,
            created_at__gte=one_hour_ago
        ).count()

        if tx_count >= SUSPICIOUS_TX_COUNT_1H:
            self.score += 20
            self.reasons.append("High frequency transactions")

    def check_agent_risk(self):
        if self.transaction.agent:
            if self.transaction.agent.is_flagged:
                self.score += 40
                self.reasons.append("Flagged agent involved")

    # ------------------------------
    # FINAL RISK LEVEL
    # ------------------------------

    def calculate_level(self):

        if self.score >= 80:
            return RiskLevel.CRITICAL
        elif self.score >= 60:
            return RiskLevel.HIGH
        elif self.score >= 30:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW