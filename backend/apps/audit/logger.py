# backend/apps/audit/logger.py

import json
import hashlib
from datetime import datetime
from django.utils import timezone
from django.conf import settings

from .models import AuditLog
from apps.ipfs_storage.uploader import upload_to_ipfs


class AuditLogger:
    """
    FubaPay Secure Audit Logger
    Logs every critical system action with hashing and optional IPFS storage
    """

    @staticmethod
    def generate_hash(data: dict) -> str:
        """
        Generate SHA256 hash of log data
        """
        encoded = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def log_event(
        action: str,
        user=None,
        metadata: dict = None,
        ip_address: str = None,
        store_on_ipfs: bool = False,
    ):
        """
        Create secure audit log entry
        """

        if metadata is None:
            metadata = {}

        log_data = {
            "action": action,
            "user_id": user.id if user else None,
            "email": user.email if user else None,
            "ip_address": ip_address,
            "metadata": metadata,
            "timestamp": str(timezone.now()),
        }

        # Generate secure hash
        log_hash = AuditLogger.generate_hash(log_data)

        # Save to database
        audit_entry = AuditLog.objects.create(
            action=action,
            user=user,
            ip_address=ip_address,
            metadata=metadata,
            log_hash=log_hash,
        )

        # Optional: Store encrypted log on IPFS
        ipfs_hash = None
        if store_on_ipfs:
            try:
                ipfs_hash = upload_to_ipfs(log_data)
                audit_entry.ipfs_hash = ipfs_hash
                audit_entry.save(update_fields=["ipfs_hash"])
            except Exception as e:
                print("IPFS upload failed:", e)

        return {
            "status": "logged",
            "log_id": audit_entry.id,
            "hash": log_hash,
            "ipfs_hash": ipfs_hash,
        }