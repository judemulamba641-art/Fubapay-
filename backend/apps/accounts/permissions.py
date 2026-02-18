from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


# =====================================================
# ROLE PERMISSIONS
# =====================================================

class IsAdminUserRole(BasePermission):
    """
    Allow only admin users
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsAgent(BasePermission):
    """
    Allow only agents
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "agent"


class IsMerchant(BasePermission):
    """
    Allow only merchants
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "merchant"


class IsClient(BasePermission):
    """
    Allow only clients
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "client"


# =====================================================
# TRUST & RISK PERMISSIONS
# =====================================================

class IsNotFlagged(BasePermission):
    """
    Deny access if user is flagged as risky
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.risk_flag:
            raise PermissionDenied("Account temporarily restricted due to risk detection.")

        return True


class CanMakeTransaction(BasePermission):
    """
    Check if user can perform a transaction
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.risk_flag:
            raise PermissionDenied("Transaction blocked: risk flag detected.")

        amount = request.data.get("amount")

        if not amount:
            return True  # Let serializer validate missing field

        try:
            amount = float(amount)
        except ValueError:
            return False

        if amount > float(request.user.single_transaction_limit):
            raise PermissionDenied("Transaction exceeds single transaction limit.")

        return True


# =====================================================
# COMBINED PERMISSION EXAMPLES
# =====================================================

class IsAgentAndSafe(BasePermission):
    """
    Agent + not flagged
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "agent"
            and not request.user.risk_flag
        )


class IsMerchantAndSafe(BasePermission):
    """
    Merchant + not flagged
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "merchant"
            and not request.user.risk_flag
        )