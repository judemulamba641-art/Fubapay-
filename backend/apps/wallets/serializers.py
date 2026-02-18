from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from django.db import transaction as db_transaction

from .models import (
    BlockchainNetwork,
    Token,
    Wallet,
    WalletBalance,
    InternalLedger,
    BlockchainTransaction,
    AMLFlag,
    WalletStatus,
    TransactionStatus,
)


# ==========================================================
# BLOCKCHAIN NETWORK
# ==========================================================

class BlockchainNetworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockchainNetwork
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "last_block_synced",
        )


# ==========================================================
# TOKEN
# ==========================================================

class TokenSerializer(serializers.ModelSerializer):

    network = BlockchainNetworkSerializer(read_only=True)

    class Meta:
        model = Token
        fields = "__all__"
        read_only_fields = ("id",)


# ==========================================================
# WALLET BALANCE
# ==========================================================

class WalletBalanceSerializer(serializers.ModelSerializer):

    token = TokenSerializer(read_only=True)
    total_balance = serializers.SerializerMethodField()

    class Meta:
        model = WalletBalance
        fields = (
            "id",
            "token",
            "available_balance",
            "locked_balance",
            "total_balance",
            "last_synced_block",
            "last_synced_at",
        )

    def get_total_balance(self, obj):
        return obj.total_balance()


# ==========================================================
# WALLET
# ==========================================================

class WalletSerializer(serializers.ModelSerializer):

    balances = WalletBalanceSerializer(many=True, read_only=True)
    network = BlockchainNetworkSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = (
            "id",
            "address",
            "wallet_type",
            "status",
            "network",
            "risk_score",
            "aml_flag",
            "daily_withdraw_limit",
            "monthly_withdraw_limit",
            "balances",
            "created_at",
        )

        read_only_fields = (
            "id",
            "risk_score",
            "aml_flag",
            "created_at",
        )


# ==========================================================
# CREATE WALLET (ADMIN / SYSTEM)
# ==========================================================

class CreateWalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = (
            "user",
            "network",
            "wallet_type",
            "address",
            "private_key_encrypted",
        )

    def validate(self, data):

        if data["wallet_type"] == "USER" and not data.get("user"):
            raise serializers.ValidationError("User wallet must have a user.")

        return data


# ==========================================================
# INTERNAL LEDGER
# ==========================================================

class InternalLedgerSerializer(serializers.ModelSerializer):

    class Meta:
        model = InternalLedger
        fields = "__all__"
        read_only_fields = ("id", "created_at")


# ==========================================================
# BLOCKCHAIN TRANSACTION
# ==========================================================

class BlockchainTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockchainTransaction
        fields = "__all__"
        read_only_fields = (
            "id",
            "status",
            "confirmations",
            "risk_score",
            "created_at",
        )


# ==========================================================
# WITHDRAW SERIALIZER
# ==========================================================

class WithdrawSerializer(serializers.Serializer):

    wallet_id = serializers.UUIDField()
    token_id = serializers.UUIDField()
    to_address = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=40, decimal_places=18)

    def validate(self, data):

        try:
            wallet = Wallet.objects.get(id=data["wallet_id"])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found.")

        if wallet.status != WalletStatus.ACTIVE:
            raise serializers.ValidationError("Wallet is not active.")

        if wallet.aml_flag in [AMLFlag.SANCTIONED, AMLFlag.HIGH_RISK]:
            raise serializers.ValidationError("Wallet blocked due to AML risk.")

        try:
            balance = WalletBalance.objects.get(
                wallet=wallet,
                token_id=data["token_id"]
            )
        except WalletBalance.DoesNotExist:
            raise serializers.ValidationError("Token not found in wallet.")

        if balance.available_balance < data["amount"]:
            raise serializers.ValidationError("Insufficient balance.")

        if wallet.daily_withdraw_limit > 0:
            if data["amount"] > wallet.daily_withdraw_limit:
                raise serializers.ValidationError("Daily withdraw limit exceeded.")

        data["wallet"] = wallet
        data["balance"] = balance

        return data

    def save(self):

        wallet = self.validated_data["wallet"]
        balance = self.validated_data["balance"]
        amount = self.validated_data["amount"]

        with db_transaction.atomic():

            balance.available_balance -= amount
            balance.locked_balance += amount
            balance.save()

            ledger_entry = InternalLedger.objects.create(
                wallet=wallet,
                token=balance.token,
                ledger_type="DEBIT",
                amount=amount,
                balance_after=balance.available_balance,
                reference="WITHDRAW_INIT",
                description="Withdrawal initiated",
            )

        return ledger_entry


# ==========================================================
# DEPOSIT SERIALIZER
# ==========================================================

class DepositSerializer(serializers.Serializer):

    wallet_id = serializers.UUIDField()
    token_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=40, decimal_places=18)

    def validate(self, data):

        try:
            wallet = Wallet.objects.get(id=data["wallet_id"])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found.")

        data["wallet"] = wallet
        return data

    def save(self):

        wallet = self.validated_data["wallet"]
        amount = self.validated_data["amount"]
        token_id = self.validated_data["token_id"]

        balance, _ = WalletBalance.objects.get_or_create(
            wallet=wallet,
            token_id=token_id,
            defaults={"available_balance": Decimal("0")}
        )

        with db_transaction.atomic():

            balance.available_balance += amount
            balance.save()

            ledger_entry = InternalLedger.objects.create(
                wallet=wallet,
                token=balance.token,
                ledger_type="CREDIT",
                amount=amount,
                balance_after=balance.available_balance,
                reference="DEPOSIT",
                description="Deposit credited",
            )

        return ledger_entry