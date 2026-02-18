"""
Production settings for FubaPay
"""

from .base import *
import os


# =====================================================
# CORE SECURITY
# =====================================================

DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")


# =====================================================
# DATABASE (PostgreSQL recommandé en prod)
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}


# =====================================================
# SECURITY HEADERS
# =====================================================

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# =====================================================
# CSRF TRUSTED ORIGINS
# =====================================================

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")


# =====================================================
# STATIC & MEDIA FILES
# =====================================================

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# =====================================================
# EMAIL CONFIGURATION
# =====================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


# =====================================================
# JWT SECURITY
# =====================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


# =====================================================
# FUBAPAY LIMITS (NO KYC MODE)
# =====================================================

DAILY_TRANSACTION_LIMIT = float(os.getenv("DAILY_TRANSACTION_LIMIT", 500))
MAX_SINGLE_TRANSACTION = float(os.getenv("MAX_SINGLE_TRANSACTION", 200))
AGENT_INITIAL_LIMIT = float(os.getenv("AGENT_INITIAL_LIMIT", 300))


# =====================================================
# BLOCKCHAIN SETTINGS
# =====================================================

BLOCKCHAIN_NETWORK = os.getenv("BLOCKCHAIN_NETWORK")
USDC_CONTRACT_ADDRESS = os.getenv("USDC_CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = os.getenv("CHAIN_ID")


# =====================================================
# IPFS SETTINGS
# =====================================================

IPFS_API_URL = os.getenv("IPFS_API_URL")
IPFS_PROJECT_ID = os.getenv("IPFS_PROJECT_ID")
IPFS_PROJECT_SECRET = os.getenv("IPFS_PROJECT_SECRET")


# =====================================================
# AI ENGINE SETTINGS
# =====================================================

AI_RISK_THRESHOLD = float(os.getenv("AI_RISK_THRESHOLD", 0.75))
AI_SCORING_ENABLED = os.getenv("AI_SCORING_ENABLED", "True") == "True"


# =====================================================
# LOGGING (IMPORTANT POUR FINTECH)
# =====================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "fubapay.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "WARNING",
    },
}