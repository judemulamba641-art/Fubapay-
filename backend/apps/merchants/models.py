# backend/apps/merchants/models.py

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------------------------
# NETWORK OPTIONS
# --------------------------------------------
NETWORK_CHOICES = (
    ("polygon", "Polygon"),
    ("base", "Base"),
    ("tron", "Tron"),
    ("ethereum", "Ethereum"),
)


STATUS_CHOICES = (
    ("active", "Active"),
    ("restricted", "Restricted"),
    ("suspended", "Suspended"),
)


RISK_LEVELS = (
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
)


# --------------------------------------------
# MAIN MERCHANT PROFILE
# --------------------------------------------
class MerchantProfile(models.Model):
    """
    Advanced Merchant Model for FubaPay
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="merchant_profile"
    )

    business_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    business_category = models.CharField(max_length=150, blank=True, null=True)

    # QR Payment ID
    merchant_code = models.CharField(
        max_length=20,
        unique=True
    )

    # ------------------------------------
    # Payment Configuration
    # ------------------------------------
    default_network = models.CharField(
        max_length=20,
        choices=NETWORK_CHOICES,
        default="polygon"
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.20")  # 0.20%
    )

    accept_usdc = models.BooleanField(default=True)

    # ------------------------------------
    # Limits
    # ------------------------------------
    daily_limit = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("1000")
    )

    monthly_limit = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("10000")
    )

    # ------------------------------------
    # AI & Risk Management
    # ------------------------------------
    ai_score = models.IntegerField(default=50)
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVELS,
        default="low"
    )

    auto_freeze = models.BooleanField(default=False)

    # ------------------------------------
    # Statistics Cache (Performance)
    # ------------------------------------
    total_volume = models.DecimalField(
        max_digits=24,
        decimal_places=6,
        default=Decimal("0")
    )

    total_transactions = models.IntegerField(default=0)
    total_commission_paid = models.DecimalField(
        max_digits=24,
        decimal_places=6,
        default=Decimal("0")
    )

    # ------------------------------------
    # Status
    # ------------------------------------
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    # ------------------------------------
    # Metadata
    # ------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------
    # Methods
    # ------------------------------------
    def __str__(self):
        return self.business_name

    def is_active(self):
        return self.status == "active"

    def update_ai_score(self, score: int):
        self.ai_score = max(0, min(100, score))
        self.save(update_fields=["ai_score"])

    def increase_volume(self, amount: Decimal):
        self.total_volume += amount
        self.total_transactions += 1
        self.save(update_fields=["total_volume", "total_transactions"])

    def apply_commission(self, amount: Decimal) -> Decimal:
        commission = (amount * self.commission_rate) / 100
        self.total_commission_paid += commission
        self.save(update_fields=["total_commission_paid"])
        return commission

    def check_risk_auto_freeze(self):
        if self.ai_score < 30:
            self.status = "restricted"
            self.auto_freeze = True
            self.save(update_fields=["status", "auto_freeze"])


# --------------------------------------------
# MULTI-WALLET SUPPORT
# --------------------------------------------
class MerchantWallet(models.Model):
    """
    Each merchant can have multiple wallets on different networks
    """

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="wallets"
    )

    network = models.CharField(
        max_length=20,
        choices=NETWORK_CHOICES
    )

    wallet_address = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("merchant", "network")

    def __str__(self):
        return f"{self.merchant.business_name} - {self.network}"