from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import (
    Transaction,
    QRCode,
    TransactionDispute,
    TransactionStatus
)

from .serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    QRCodeSerializer,
    TransactionDisputeSerializer
)

from .risk import RiskEngine


# ==========================================================
# TRANSACTION VIEWSET
# ==========================================================

class TransactionViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related(
            "sender",
            "receiver",
            "wallet_from",
            "wallet_to",
            "agent",
            "qr_code"
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return TransactionCreateSerializer
        return TransactionSerializer

    # -----------------------------------
    # CREATE TRANSACTION
    # -----------------------------------

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()

        return Response(
            TransactionSerializer(transaction).data,
            status=status.HTTP_201_CREATED
        )

    # -----------------------------------
    # MANUAL AI REVIEW APPROVAL
    # -----------------------------------

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):

        transaction = self.get_object()

        if transaction.status != TransactionStatus.AI_REVIEW:
            return Response(
                {"error": "Transaction not under AI review."},
                status=400
            )

        transaction.status = TransactionStatus.APPROVED
        transaction.save(update_fields=["status"])

        return Response({"message": "Transaction approved."})

    # -----------------------------------
    # REJECT TRANSACTION
    # -----------------------------------

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):

        transaction = self.get_object()

        if transaction.status not in [
            TransactionStatus.AI_REVIEW,
            TransactionStatus.PENDING
        ]:
            return Response(
                {"error": "Transaction cannot be rejected."},
                status=400
            )

        transaction.status = TransactionStatus.REJECTED
        transaction.save(update_fields=["status"])

        return Response({"message": "Transaction rejected."})

    # -----------------------------------
    # CONFIRM ON-CHAIN
    # -----------------------------------

    @action(detail=True, methods=["post"])
    def confirm_onchain(self, request, pk=None):

        transaction = self.get_object()

        if transaction.status != TransactionStatus.APPROVED:
            return Response(
                {"error": "Transaction not approved."},
                status=400
            )

        tx_hash = request.data.get("tx_hash")
        block_number = request.data.get("block_number")

        if not tx_hash:
            return Response(
                {"error": "tx_hash required."},
                status=400
            )

        transaction.status = TransactionStatus.CONFIRMED
        transaction.tx_hash = tx_hash
        transaction.block_number = block_number
        transaction.executed_at = timezone.now()
        transaction.save()

        return Response({"message": "Transaction confirmed on-chain."})

    # -----------------------------------
    # USER TRANSACTION STATS
    # -----------------------------------

    @action(detail=False, methods=["get"])
    def stats(self, request):

        user = request.user

        total_sent = Transaction.objects.filter(
            sender=user,
            status=TransactionStatus.CONFIRMED
        ).count()

        total_received = Transaction.objects.filter(
            receiver=user,
            status=TransactionStatus.CONFIRMED
        ).count()

        return Response({
            "total_sent": total_sent,
            "total_received": total_received
        })


# ==========================================================
# QR CODE VIEWSET
# ==========================================================

class QRCodeViewSet(viewsets.ModelViewSet):

    serializer_class = QRCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QRCode.objects.filter(
            merchant__user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            merchant=self.request.user.merchantprofile
        )


# ==========================================================
# DISPUTE VIEWSET
# ==========================================================

class TransactionDisputeViewSet(viewsets.ModelViewSet):

    serializer_class = TransactionDisputeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TransactionDispute.objects.filter(
            opened_by=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            opened_by=self.request.user
        )