# backend/apps/notifications/push.py

import uuid
import logging
from typing import List

from django.conf import settings
from django.utils import timezone

import firebase_admin
from firebase_admin import credentials, messaging

from apps.audit.logger import AuditLogger
from apps.notifications.models import PushNotification
from apps.security.encrypt import EncryptionService

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Firebase Initialization (Singleton)
# --------------------------------------------------

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


# --------------------------------------------------
# Push Service
# --------------------------------------------------

class PushService:
    """
    Enterprise-grade Push Notification Service
    - Secure
    - Logged
    - Retry-ready
    - Multi-device
    """

    def __init__(self):
        self.max_retry = getattr(settings, "PUSH_MAX_RETRY", 3)
        self.encryption = EncryptionService()

    # --------------------------------------------------
    # Core Sender
    # --------------------------------------------------

    def _send_to_tokens(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: dict = None,
        user=None,
        priority="high",
        audit_action=None
    ):
        """
        Core push sending logic with tracking & audit
        """

        if not tokens:
            return {"status": "no_tokens"}

        notification_id = str(uuid.uuid4())

        encrypted_tokens = [
            self.encryption.decrypt(token) for token in tokens
        ]

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                "notification_id": notification_id,
                **(data or {})
            },
            tokens=encrypted_tokens,
            android=messaging.AndroidConfig(
                priority=priority,
                ttl=3600
            ),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"}
            ),
        )

        response = messaging.send_multicast(message)

        # Save DB record
        PushNotification.objects.create(
            notification_id=notification_id,
            title=title,
            body=body,
            success_count=response.success_count,
            failure_count=response.failure_count,
            sent_at=timezone.now(),
        )

        # Audit log
        if user and audit_action:
            AuditLogger.log_event(
                action=audit_action,
                user=user,
                metadata={
                    "notification_id": notification_id,
                    "success": response.success_count,
                    "failure": response.failure_count,
                },
                store_on_ipfs=False
            )

        return {
            "notification_id": notification_id,
            "success": response.success_count,
            "failure": response.failure_count
        }

    # --------------------------------------------------
    # User Notifications
    # --------------------------------------------------

    def send_payment_received(self, user, amount):
        tokens = user.get_push_tokens()

        return self._send_to_tokens(
            tokens=tokens,
            title="Paiement reçu 💰",
            body=f"Vous avez reçu {amount} USDC.",
            data={"type": "payment_received"},
            user=user,
            audit_action="PUSH_PAYMENT_RECEIVED"
        )

    def send_security_alert(self, user, message):
        tokens = user.get_push_tokens()

        return self._send_to_tokens(
            tokens=tokens,
            title="Alerte sécurité ⚠️",
            body=message,
            data={"type": "security_alert"},
            user=user,
            audit_action="PUSH_SECURITY_ALERT"
        )

    def send_account_freeze(self, user, reason):
        tokens = user.get_push_tokens()

        return self._send_to_tokens(
            tokens=tokens,
            title="Compte restreint 🔒",
            body=f"Votre compte a été temporairement restreint : {reason}",
            data={"type": "account_freeze"},
            user=user,
            audit_action="PUSH_ACCOUNT_FREEZE"
        )

    # --------------------------------------------------
    # Merchant Notification
    # --------------------------------------------------

    def send_merchant_sale(self, merchant, amount):
        tokens = merchant.get_push_tokens()

        return self._send_to_tokens(
            tokens=tokens,
            title="Nouvelle vente 🎉",
            body=f"Vous avez réalisé une vente de {amount} USDC.",
            data={"type": "merchant_sale"},
            user=merchant.user,
            audit_action="PUSH_MERCHANT_SALE"
        )

    # --------------------------------------------------
    # Admin Broadcast
    # --------------------------------------------------

    def broadcast_to_all(self, tokens: List[str], title: str, body: str):
        return self._send_to_tokens(
            tokens=tokens,
            title=title,
            body=body,
            data={"type": "broadcast"},
            priority="normal",
        )