import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django_cryptography.fields import encrypt


# ==========================================================
# ENUMS
# ==========================================================

class NetworkType(models.TextChoices):
    ETHEREUM = "ETHEREUM", "Ethereum"
    POLYGON = "POLYGON", "Polygon"
    BSC = "BSC", "Binance Smart Chain"
    ARBITRUM = "ARBITRUM", "Arbitrum"
    BASE = "BASE", "Base"


class WalletType(models.TextChoices):
    USER = "USER", "User"
    HOT = "HOT", "Hot Wallet"
    COLD = "COLD", "Cold Wallet"
    TREASURY = "TREASURY", "Treasury"
    FEES = "FEES", "Fee Collector"


class WalletStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    FROZEN = "FROZEN", "Frozen"
    SUSPENDED = "SUSPENDED", "Suspended"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"


class TokenType(models.TextChoices):
    NATIVE = "NATIVE", "Native"
    ERC20 = "ERC20", "ERC20"
    BEP20 = "BEP20", "BEP20"


class TransactionDirection(models.TextChoices):
    IN = "IN", "Incoming"
    OUT = "OUT", "Outgoing"


class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"
    REJECTED = "REJECTED", "Rejected"


class LedgerType(models.TextChoices):
    DEBIT = "DEBIT", "Debit"
    CREDIT = "CREDIT", "Credit"


class AMLFlag(models.TextChoices):
    NONE = "NONE", "None"
    SUSPICIOUS = "SUSPICIOUS", "Suspicious"
    SANCTIONED = "SANCTIONED", "Sanctioned"
    HIGH_RISK = "HIGH_RISK", "High Risk"


# ==========================================================
# BLOCKCHAIN NETWORK
# ==========================================================

class BlockchainNetwork(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=30, choices=NetworkType.choices)
    chain_id = models.IntegerField(unique=True)

    rpc_primary = models.URLField()
    rpc_secondary = models.URLField(blank=True, null=True)
    rpc_tertiary = models.URLField(blank=True, null=True)

    explorer_url = models.URLField()

    is_active = models.BooleanField(default=True)
    confirmations_required = models.IntegerField(default=3)

    last_block_synced = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.chain_id})"


# ==========================================================
# TOKEN
# ==========================================================

class Token(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    network = models.ForeignKey(
        BlockchainNetwork,
        on_delete=models.CASCADE,
        related_name="tokens"
    )

    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=15)
    decimals = models.IntegerField(default=18)

    contract_address = models.CharField(max_length=255, blank=True, null=True)

    token_type = models.CharField(
        max_length=10,
        choices=TokenType.choices,
        default=TokenType.ERC20
    )

    is_stablecoin = models.BooleanField(default=False)
    withdrawal_fee = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal("0.0")
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("network", "symbol")

    def __str__(self):
        return f"{self.symbol} - {self.network.name}"


# ==========================================================
# WALLET
# ==========================================================

class Wallet(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallets",
        null=True,
        blank=True
    )

    network = models.ForeignKey(
        BlockchainNetwork,
        on_delete=models.CASCADE,
        related_name="wallets"
    )

    wallet_type = models.CharField(max_length=15, choices=WalletType.choices)
    status = models.CharField(max_length=20, choices=WalletStatus.choices, default=WalletStatus.ACTIVE)

    address = models.CharField(max_length=255, unique=True)
    private_key_encrypted = encrypt(models.TextField(blank=True, null=True))

    nonce = models.BigIntegerField(default=0)

    risk_score = models.FloatField(default=0.0)
    aml_flag = models.CharField(max_length=20, choices=AMLFlag.choices, default=AMLFlag.NONE)

    is_whitelisted = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

    daily_withdraw_limit = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal("0.0"))
    monthly_withdraw_limit = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal("0.0"))

    total_received = models.DecimalField(max_digits=40, decimal_places=18, default=Decimal("0"))
    total_sent = models.DecimalField(max_digits=40, decimal_places=18, default=Decimal("0"))

    last_activity_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["address"]),
            models.Index(fields=["wallet_type"]),
            models.Index(fields=["aml_flag"]),
        ]

    def freeze(self):
        self.status = WalletStatus.FROZEN
        self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.address[:10]}..."


# ==========================================================
# WALLET BALANCE
# ==========================================================

class WalletBalance(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="balances")
    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    available_balance = models.DecimalField(max_digits=40, decimal_places=18, default=Decimal("0"))
    locked_balance = models.DecimalField(max_digits=40, decimal_places=18, default=Decimal("0"))

    last_synced_block = models.BigIntegerField(default=0)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("wallet", "token")

    def total_balance(self):
        return self.available_balance + self.locked_balance


# ==========================================================
# INTERNAL LEDGER (OFF-CHAIN ACCOUNTING)
# ==========================================================

class InternalLedger(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    ledger_type = models.CharField(max_length=10, choices=LedgerType.choices)

    amount = models.DecimalField(max_digits=40, decimal_places=18)
    balance_after = models.DecimalField(max_digits=40, decimal_places=18)

    reference = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["wallet"]),
            models.Index(fields=["reference"]),
        ]


# ==========================================================
# BLOCKCHAIN TRANSACTION TRACKING
# ==========================================================

class BlockchainTransaction(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    tx_hash = models.CharField(max_length=255, db_index=True)
    block_number = models.BigIntegerField(null=True, blank=True)

    from_address = models.CharField(max_length=255)
    to_address = models.CharField(max_length=255)

    amount = models.DecimalField(max_digits=40, decimal_places=18)

    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)

    confirmations = models.IntegerField(default=0)

    direction = models.CharField(max_length=5, choices=TransactionDirection.choices)
    status = models.CharField(max_length=15, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    risk_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tx_hash"]),
            models.Index(fields=["status"]),
            models.Index(fields=["confirmations"]),
        ]

    def is_confirmed(self):
        return self.status == TransactionStatus.CONFIRMED