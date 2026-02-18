"""
WSGI config for FubaPay project.

It exposes the WSGI callable as a module-level variable named `application`.

Used for production servers like:
- Gunicorn
- uWSGI
- PythonAnywhere
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application


# --------------------------------------------------
# Load environment variables from .env if present
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key, value)


# --------------------------------------------------
# Set default settings module
# --------------------------------------------------

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
)


# --------------------------------------------------
# Create WSGI application
# --------------------------------------------------

application = get_wsgi_application()