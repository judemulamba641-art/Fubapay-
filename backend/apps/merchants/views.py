# backend/apps/merchants/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404

from .models import MerchantProfile, MerchantWallet
from .dashboard import MerchantDashboardService
from apps.audit.logger import AuditLogger


# -------------------------------------------------
# CREATE MERCHANT PROFILE
# -------------------------------------------------
class CreateMerchantProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if hasattr(user, "merchant_profile"):
            return Response(
                {"error": "Merchant profile already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data

        merchant = MerchantProfile.objects.create(
            user=user,
            business_name=data.get("business_name"),
            description=data.get("description"),
            business_category=data.get("business_category"),
            merchant_code=data.get("merchant_code"),
        )

        AuditLogger.log_event(
            action="MERCHANT_CREATED",
            user=user,
            metadata={"merchant_id": str(merchant.id)},
            ip_address=request.META.get("REMOTE_ADDR"),
            store_on_ipfs=True
        )

        return Response(
            {"message": "Merchant profile created successfully"},
            status=status.HTTP_201_CREATED
        )


# -------------------------------------------------
# GET MERCHANT PROFILE
# -------------------------------------------------
class MerchantProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = get_object_or_404(
            MerchantProfile,
            user=request.user
        )

        data = {
            "id": merchant.id,
            "business_name": merchant.business_name,
            "description": merchant.description,
            "category": merchant.business_category,
            "commission_rate": merchant.commission_rate,
            "ai_score": merchant.ai_score,
            "risk_level": merchant.risk_level,
            "status": merchant.status,
            "total_volume": merchant.total_volume,
            "total_transactions": merchant.total_transactions,
        }

        return Response(data)


# -------------------------------------------------
# UPDATE MERCHANT SETTINGS
# -------------------------------------------------
class UpdateMerchantSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        merchant = get_object_or_404(
            MerchantProfile,
            user=request.user
        )

        merchant.description = request.data.get(
            "description", merchant.description
        )

        merchant.business_category = request.data.get(
            "business_category", merchant.business_category
        )

        merchant.save()

        AuditLogger.log_event(
            action="MERCHANT_UPDATED",
            user=request.user,
            metadata={"merchant_id": str(merchant.id)},
            ip_address=request.META.get("REMOTE_ADDR"),
            store_on_ipfs=False
        )

        return Response({"message": "Merchant updated"})


# -------------------------------------------------
# MERCHANT DASHBOARD
# -------------------------------------------------
class MerchantDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = get_object_or_404(
            MerchantProfile,
            user=request.user
        )

        dashboard = MerchantDashboardService(request.user)
        data = dashboard.get_dashboard_data()

        return Response(data)


# -------------------------------------------------
# ADD WALLET
# -------------------------------------------------
class AddMerchantWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        merchant = get_object_or_404(
            MerchantProfile,
            user=request.user
        )

        wallet = MerchantWallet.objects.create(
            merchant=merchant,
            network=request.data.get("network"),
            wallet_address=request.data.get("wallet_address"),
            is_default=request.data.get("is_default", False)
        )

        AuditLogger.log_event(
            action="MERCHANT_WALLET_ADDED",
            user=request.user,
            metadata={
                "network": wallet.network,
                "wallet_address": wallet.wallet_address
            },
            ip_address=request.META.get("REMOTE_ADDR"),
            store_on_ipfs=True
        )

        return Response(
            {"message": "Wallet added successfully"},
            status=status.HTTP_201_CREATED
        )


# -------------------------------------------------
# LIST WALLETS
# -------------------------------------------------
class MerchantWalletListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchant = get_object_or_404(
            MerchantProfile,
            user=request.user
        )

        wallets = merchant.wallets.all()

        data = [
            {
                "id": wallet.id,
                "network": wallet.network,
                "wallet_address": wallet.wallet_address,
                "is_default": wallet.is_default
            }
            for wallet in wallets
        ]

        return Response(data)