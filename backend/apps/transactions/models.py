import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


# -------------------------
# ENUMS
# -------------------------

class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    AI_REVIEW = "AI_REVIEW", "AI Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    PROCESSING = "PROCESSING", "Processing On-chain"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"
    DISPUTED = "DISPUTED", "Disputed"
    REFUNDED = "REFUNDED", "Refunded"
    CANCELLED = "CANCELLED", "Cancelled"


class TransactionType(models.TextChoices):
    QR_PAYMENT = "QR_PAYMENT", "QR Payment"
    AGENT_EXCHANGE = "AGENT_EXCHANGE", "Agent Exchange"
    MERCHANT_PAYMENT = "MERCHANT_PAYMENT", "Merchant Payment"
    P2P = "P2P", "Peer to Peer"


class RiskLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


# -------------------------
# QR CODE MODEL
# -------------------------

class QRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    merchant = models.ForeignKey(
        "merchants.MerchantProfile",
        on_delete=models.CASCADE,
        related_name="qr_codes"
    )

    label = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True
    )

    currency = models.CharField(max_length=10, default="USDC")

    is_dynamic = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"{self.label} - {self.merchant.user.email}"


# -------------------------
# MAIN TRANSACTION MODEL
# -------------------------

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reference = models.CharField(
        max_length=32,
        unique=True,
        editable=False
    )

    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_transactions"
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_transactions"
    )

    wallet_from = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.SET_NULL,
        null=True,
        related_name="outgoing_transactions"
    )

    wallet_to = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.SET_NULL,
        null=True,
        related_name="incoming_transactions"
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6
    )

    currency = models.CharField(max_length=10, default="USDC")

    network = models.CharField(max_length=50, default="Polygon")

    gas_fee = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0.0")
    )

    tx_hash = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    block_number = models.BigIntegerField(null=True, blank=True)

    confirmations = models.IntegerField(default=0)

    # IA Risk Scoring
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW
    )

    ai_decision_reason = models.TextField(blank=True, null=True)

    # IPFS proof
    ipfs_hash = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # Agent involved
    agent = models.ForeignKey(
        "agents.AgentProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # QR linked
    qr_code = models.ForeignKey(
        QRCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["risk_level"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def mark_processing(self):
        self.status = TransactionStatus.PROCESSING
        self.save(update_fields=["status"])

    def mark_confirmed(self, tx_hash, block_number):
        self.status = TransactionStatus.CONFIRMED
        self.tx_hash = tx_hash
        self.block_number = block_number
        self.executed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency}"


# -------------------------
# DISPUTE SYSTEM
# -------------------------

class TransactionDispute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="disputes"
    )

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolution_note = models.TextField(blank=True, null=True)

    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Dispute - {self.transaction.reference}"