# backend/apps/notifications/email.py

import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from apps.audit.logger import AuditLogger


class EmailService:
    """
    Advanced Email Service for FubaPay
    Scalable, secure, and audit-ready
    """

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.timeout = getattr(settings, "EMAIL_TIMEOUT", 10)

    # --------------------------------------------------
    # Core Send Method
    # --------------------------------------------------
    def _send(self, subject, to_email, template, context, user=None, audit_action=None):
        """
        Send templated email with tracking & audit
        """

        tracking_id = str(uuid.uuid4())

        # Inject tracking pixel
        tracking_pixel = f"""
        <img src="{settings.EMAIL_TRACKING_DOMAIN}/{tracking_id}"
             width="1" height="1" />
        """

        context["tracking_pixel"] = tracking_pixel
        context["year"] = timezone.now().year

        html_content = render_to_string(template, context)
        text_content = strip_tags(html_content)

        connection = get_connection(timeout=self.timeout)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=self.from_email,
            to=[to_email],
            connection=connection,
        )

        email.attach_alternative(html_content, "text/html")

        # Security headers
        email.extra_headers = {
            "X-FubaPay-Notification": "true",
            "X-Tracking-ID": tracking_id,
        }

        email.send()

        # Audit log
        if user and audit_action:
            AuditLogger.log_event(
                action=audit_action,
                user=user,
                metadata={
                    "email": to_email,
                    "tracking_id": tracking_id
                },
                store_on_ipfs=False
            )

        return tracking_id

    # --------------------------------------------------
    # Payment Confirmation
    # --------------------------------------------------
    def send_payment_confirmation(self, user, amount, tx_id):
        return self._send(
            subject="Paiement confirmé sur FubaPay 💰",
            to_email=user.email,
            template="emails/payment_confirmation.html",
            context={
                "user": user,
                "amount": amount,
                "tx_id": tx_id,
            },
            user=user,
            audit_action="EMAIL_PAYMENT_SENT"
        )

    # --------------------------------------------------
    # Security Alert
    # --------------------------------------------------
    def send_security_alert(self, user, message):
        return self._send(
            subject="Alerte de sécurité FubaPay ⚠️",
            to_email=user.email,
            template="emails/security_alert.html",
            context={
                "user": user,
                "message": message,
            },
            user=user,
            audit_action="EMAIL_SECURITY_ALERT"
        )

    # --------------------------------------------------
    # Welcome Email
    # --------------------------------------------------
    def send_welcome_email(self, user):
        return self._send(
            subject="Bienvenue sur FubaPay 🚀",
            to_email=user.email,
            template="emails/welcome.html",
            context={
                "user": user,
            },
            user=user,
            audit_action="EMAIL_WELCOME_SENT"
        )

    # --------------------------------------------------
    # Risk Freeze Notification
    # --------------------------------------------------
    def send_account_freeze_notification(self, user, reason):
        return self._send(
            subject="Compte temporairement restreint 🔒",
            to_email=user.email,
            template="emails/account_freeze.html",
            context={
                "user": user,
                "reason": reason,
            },
            user=user,
            audit_action="EMAIL_ACCOUNT_FREEZE"
        )