"""
ASGI config for FubaPay project.

It exposes the ASGI callable as a module-level variable named `application`.

Used for:
- WebSockets (Django Channels)
- Async support
- Uvicorn / Daphne servers
"""

import os
from pathlib import Path

from django.core.asgi import get_asgi_application


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
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
)


# --------------------------------------------------
# Create ASGI application
# --------------------------------------------------

django_asgi_app = get_asgi_application()


# --------------------------------------------------
# Optional: Enable Channels if installed
# --------------------------------------------------

try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    import apps.notifications.routing

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                apps.notifications.routing.websocket_urlpatterns
            )
        ),
    })

except ImportError:
    # If Channels is not installed, fallback to normal ASGI
    application = django_asgi_app