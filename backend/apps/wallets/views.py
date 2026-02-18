from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404

from .models import (
    BlockchainNetwork,
    Token,
    Wallet,
    WalletBalance,
    InternalLedger,
    BlockchainTransaction,
    WalletStatus,
    TransactionStatus,
)

from .serializers import (
    BlockchainNetworkSerializer,
    TokenSerializer,
    WalletSerializer,
    CreateWalletSerializer,
    WalletBalanceSerializer,
    InternalLedgerSerializer,
    BlockchainTransactionSerializer,
    WithdrawSerializer,
    DepositSerializer,
)


# ==========================================================
# PERMISSIONS
# ==========================================================

class IsOwnerOrAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.user.is_staff:
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user

        if hasattr(obj, "wallet"):
            return obj.wallet.user == request.user

        return False


# ==========================================================
# BLOCKCHAIN NETWORK VIEWSET (ADMIN ONLY)
# ==========================================================

class BlockchainNetworkViewSet(viewsets.ModelViewSet):

    queryset = BlockchainNetwork.objects.all()
    serializer_class = BlockchainNetworkSerializer
    permission_classes = [permissions.IsAdminUser]


# ==========================================================
# TOKEN VIEWSET
# ==========================================================

class TokenViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Token.objects.filter(is_active=True)
    serializer_class = TokenSerializer
    permission_classes = [permissions.AllowAny]


# ==========================================================
# WALLET VIEWSET
# ==========================================================

class WalletViewSet(viewsets.ModelViewSet):

    queryset = Wallet.objects.select_related("network").prefetch_related("balances")
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateWalletSerializer
        return WalletSerializer

    # ------------------------------------------------------
    # FREEZE WALLET (ADMIN)
    # ------------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def freeze(self, request, pk=None):

        wallet = self.get_object()
        wallet.freeze()

        return Response({"status": "Wallet frozen"})


    # ------------------------------------------------------
    # BALANCES
    # ------------------------------------------------------

    @action(detail=True, methods=["get"])
    def balances(self, request, pk=None):

        wallet = self.get_object()
        serializer = WalletBalanceSerializer(wallet.balances.all(), many=True)
        return Response(serializer.data)


    # ------------------------------------------------------
    # LEDGER
    # ------------------------------------------------------

    @action(detail=True, methods=["get"])
    def ledger(self, request, pk=None):

        wallet = self.get_object()
        entries = InternalLedger.objects.filter(wallet=wallet).order_by("-created_at")
        serializer = InternalLedgerSerializer(entries, many=True)

        return Response(serializer.data)


    # ------------------------------------------------------
    # WITHDRAW
    # ------------------------------------------------------

    @action(detail=False, methods=["post"])
    def withdraw(self, request):

        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ledger_entry = serializer.save()

        return Response(
            {
                "message": "Withdrawal initiated",
                "ledger_id": ledger_entry.id
            },
            status=status.HTTP_201_CREATED
        )


    # ------------------------------------------------------
    # DEPOSIT (INTERNAL CREDIT)
    # ------------------------------------------------------

    @action(detail=False, methods=["post"])
    def deposit(self, request):

        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ledger_entry = serializer.save()

        return Response(
            {
                "message": "Deposit credited",
                "ledger_id": ledger_entry.id
            },
            status=status.HTTP_201_CREATED
        )


# ==========================================================
# BLOCKCHAIN TRANSACTION VIEWSET
# ==========================================================

class BlockchainTransactionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = BlockchainTransaction.objects.select_related("wallet", "token")
    serializer_class = BlockchainTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):

        if self.request.user.is_staff:
            return self.queryset

        return self.queryset.filter(wallet__user=self.request.user)

    # ------------------------------------------------------
    # MANUAL CONFIRMATION UPDATE (ADMIN WORKER)
    # ------------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def update_status(self, request, pk=None):

        tx = self.get_object()
        new_status = request.data.get("status")

        if new_status not in TransactionStatus.values:
            return Response({"error": "Invalid status"}, status=400)

        tx.status = new_status
        tx.save(update_fields=["status"])

        return Response({"status": "Transaction updated"})