# backend/apps/agents/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status

from .models import AgentProfile
from .limits import AgentLimitManager
from .scoring import AgentScoringEngine


# ==========================================
# PROFIL AGENT
# ==========================================

class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return Response(
                {"error": "Profil agent introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "email": request.user.email,
            "is_active": profile.is_active,
            "is_frozen": profile.is_frozen,
            "reputation_score": profile.reputation_score,
            "trust_level": profile.trust_level,
            "total_volume": profile.total_volume,
            "total_transactions": profile.total_transactions,
            "success_rate": profile.success_rate(),
        })


# ==========================================
# LIMITES ACTUELLES
# ==========================================

class AgentLimitsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        manager = AgentLimitManager(request.user)

        return Response({
            "daily_limit": str(manager.get_daily_limit()),
            "transaction_limit": str(manager.get_transaction_limit()),
            "today_volume": str(manager.get_today_volume()),
        })


# ==========================================
# CHECK TRANSACTION AVANT EXÉCUTION
# ==========================================

class CheckTransactionPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"error": "Montant requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        manager = AgentLimitManager(request.user)
        allowed, message = manager.can_process(amount)

        if not allowed:
            return Response(
                {"allowed": False, "reason": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "allowed": True,
            "message": message
        })


# ==========================================
# RECALCUL SCORE (ADMIN)
# ==========================================

class RecalculateScoreView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, agent_id):
        try:
            profile = AgentProfile.objects.get(id=agent_id)
        except AgentProfile.DoesNotExist:
            return Response(
                {"error": "Agent introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        scoring = AgentScoringEngine(profile.user)
        new_score = scoring.full_recalculate()

        return Response({
            "message": "Score recalculé",
            "new_score": new_score
        })


# ==========================================
# GELER / DÉGELER AGENT (ADMIN)
# ==========================================

class FreezeAgentView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, agent_id):

        try:
            profile = AgentProfile.objects.get(id=agent_id)
        except AgentProfile.DoesNotExist:
            return Response(
                {"error": "Agent introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get("action")

        if action == "freeze":
            profile.freeze()
            return Response({"message": "Agent gelé"})

        elif action == "unfreeze":
            profile.unfreeze()
            return Response({"message": "Agent dégelé"})

        return Response(
            {"error": "Action invalide"},
            status=status.HTTP_400_BAD_REQUEST
        )