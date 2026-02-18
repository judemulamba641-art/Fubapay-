from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from .models import (
    Transaction,
    QRCode,
    TransactionDispute,
    TransactionStatus,
    TransactionType
)

from .risk import RiskEngine


# --------------------------------------
# QR CODE SERIALIZER
# --------------------------------------

class QRCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = QRCode
        fields = [
            "id",
            "merchant",
            "label",
            "amount",
            "currency",
            "is_dynamic",
            "is_active",
            "expires_at",
            "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        if data.get("expires_at") and data["expires_at"] < timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        return data


# --------------------------------------
# TRANSACTION CREATE SERIALIZER
# --------------------------------------

class TransactionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = [
            "type",
            "receiver",
            "wallet_from",
            "wallet_to",
            "amount",
            "currency",
            "network",
            "agent",
            "qr_code",
            "metadata"
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate(self, data):

        request = self.context["request"]
        sender = request.user

        # Prevent self transfer
        if sender == data.get("receiver"):
            raise serializers.ValidationError("Cannot send funds to yourself.")

        # QR validation
        qr = data.get("qr_code")
        if qr:
            if not qr.is_valid():
                raise serializers.ValidationError("QR Code expired or inactive.")

            if not qr.is_dynamic and qr.amount:
                if data["amount"] != qr.amount:
                    raise serializers.ValidationError(
                        "Amount must match fixed QR code value."
                    )

        # Wallet ownership validation
        wallet_from = data.get("wallet_from")
        if wallet_from.user != sender:
            raise serializers.ValidationError("Invalid wallet ownership.")

        return data

    def create(self, validated_data):

        request = self.context["request"]
        sender = request.user

        transaction = Transaction.objects.create(
            sender=sender,
            status=TransactionStatus.PENDING,
            **validated_data
        )

        # --------------------------
        # RISK ENGINE EXECUTION
        # --------------------------
        risk_engine = RiskEngine(transaction)
        result = risk_engine.evaluate()

        transaction.risk_score = result["risk_score"]
        transaction.risk_level = result["risk_level"]
        transaction.ai_decision_reason = ", ".join(result["reasons"])

        # Auto AI review decision
        if transaction.risk_level in ["HIGH", "CRITICAL"]:
            transaction.status = TransactionStatus.AI_REVIEW
        else:
            transaction.status = TransactionStatus.APPROVED

        transaction.save()

        return transaction


# --------------------------------------
# TRANSACTION READ SERIALIZER
# --------------------------------------

class TransactionSerializer(serializers.ModelSerializer):

    sender_email = serializers.EmailField(source="sender.email", read_only=True)
    receiver_email = serializers.EmailField(source="receiver.email", read_only=True)

    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = [
            "id",
            "reference",
            "status",
            "risk_score",
            "risk_level",
            "ai_decision_reason",
            "tx_hash",
            "block_number",
            "confirmations",
            "created_at",
            "updated_at",
            "executed_at",
        ]


# --------------------------------------
# DISPUTE SERIALIZER
# --------------------------------------

class TransactionDisputeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TransactionDispute
        fields = [
            "id",
            "transaction",
            "opened_by",
            "reason",
            "is_resolved",
            "resolution_note",
            "opened_at",
            "resolved_at"
        ]
        read_only_fields = [
            "id",
            "is_resolved",
            "resolution_note",
            "opened_at",
            "resolved_at"
        ]

    def validate(self, data):
        transaction = data["transaction"]

        if transaction.status != TransactionStatus.CONFIRMED:
            raise serializers.ValidationError(
                "Only confirmed transactions can be disputed."
            )

        return data