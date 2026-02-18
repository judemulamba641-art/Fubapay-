# backend/apps/merchants/dashboard.py

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count

from apps.transactions.models import Transaction
from apps.audit.models import AuditLog


class MerchantDashboardService:
    """
    FubaPay Merchant Dashboard Logic
    Provides statistics and insights for merchant panel
    """

    def __init__(self, merchant_user):
        self.user = merchant_user
        self.now = timezone.now()

    # ----------------------------------
    # Total Revenue (All Time)
    # ----------------------------------
    def total_revenue(self):
        return (
            Transaction.objects.filter(
                merchant=self.user,
                status="completed"
            ).aggregate(total=Sum("amount"))["total"] or 0
        )

    # ----------------------------------
    # Today's Revenue
    # ----------------------------------
    def today_revenue(self):
        today = self.now.date()
        return (
            Transaction.objects.filter(
                merchant=self.user,
                status="completed",
                created_at__date=today
            ).aggregate(total=Sum("amount"))["total"] or 0
        )

    # ----------------------------------
    # Monthly Revenue
    # ----------------------------------
    def monthly_revenue(self):
        first_day = self.now.replace(day=1)
        return (
            Transaction.objects.filter(
                merchant=self.user,
                status="completed",
                created_at__gte=first_day
            ).aggregate(total=Sum("amount"))["total"] or 0
        )

    # ----------------------------------
    # Transaction Count
    # ----------------------------------
    def total_transactions(self):
        return Transaction.objects.filter(
            merchant=self.user
        ).count()

    # ----------------------------------
    # Recent Transactions
    # ----------------------------------
    def recent_transactions(self, limit=10):
        return Transaction.objects.filter(
            merchant=self.user
        ).order_by("-created_at")[:limit]

    # ----------------------------------
    # Suspicious Alerts
    # ----------------------------------
    def suspicious_alerts(self):
        return AuditLog.objects.filter(
            user=self.user,
            action__icontains="RISK"
        ).order_by("-created_at")[:5]

    # ----------------------------------
    # IA Score (simple example)
    # ----------------------------------
    def ai_score(self):
        total_tx = self.total_transactions()
        if total_tx == 0:
            return 50  # neutral

        suspicious = AuditLog.objects.filter(
            user=self.user,
            action__icontains="RISK"
        ).count()

        score = max(0, 100 - (suspicious * 5))
        return score

    # ----------------------------------
    # Global Dashboard Data
    # ----------------------------------
    def get_dashboard_data(self):
        return {
            "total_revenue": self.total_revenue(),
            "today_revenue": self.today_revenue(),
            "monthly_revenue": self.monthly_revenue(),
            "total_transactions": self.total_transactions(),
            "ai_score": self.ai_score(),
            "recent_transactions": self.recent_transactions(),
            "alerts": self.suspicious_alerts(),
        }