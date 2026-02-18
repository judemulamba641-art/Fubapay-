"""
Development settings for FubaPay
"""

from .base import *
import os


# =====================================================
# CORE SETTINGS
# =====================================================

DEBUG = True

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-change-in-production"
)

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# =====================================================
# DATABASE (SQLite for local development)
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# =====================================================
# EMAIL (Console backend for development)
# =====================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# =====================================================
# SECURITY (relaxed for development)
# =====================================================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# =====================================================
# STATIC & MEDIA
# =====================================================

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# =====================================================
# FUBAPAY LIMITS (DEV MODE)
# =====================================================

DAILY_TRANSACTION_LIMIT = float(os.getenv("DAILY_TRANSACTION_LIMIT", 1000))
MAX_SINGLE_TRANSACTION = float(os.getenv("MAX_SINGLE_TRANSACTION", 500))
AGENT_INITIAL_LIMIT = float(os.getenv("AGENT_INITIAL_LIMIT", 800))


# =====================================================
# BLOCKCHAIN SETTINGS (Test Network recommandé)
# =====================================================

BLOCKCHAIN_NETWORK = os.getenv("BLOCKCHAIN_NETWORK", "polygon-mumbai")
USDC_CONTRACT_ADDRESS = os.getenv("USDC_CONTRACT_ADDRESS", "")
RPC_URL = os.getenv("RPC_URL", "")
CHAIN_ID = os.getenv("CHAIN_ID", "80001")


# =====================================================
# IPFS SETTINGS (Local Node)
# =====================================================

IPFS_API_URL = os.getenv("IPFS_API_URL", "http://127.0.0.1:5001")
IPFS_PROJECT_ID = os.getenv("IPFS_PROJECT_ID", "")
IPFS_PROJECT_SECRET = os.getenv("IPFS_PROJECT_SECRET", "")


# =====================================================
# AI SETTINGS (More permissive in dev)
# =====================================================

AI_RISK_THRESHOLD = float(os.getenv("AI_RISK_THRESHOLD", 0.90))
AI_SCORING_ENABLED = True


# =====================================================
# LOGGING (Console for development)
# =====================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}