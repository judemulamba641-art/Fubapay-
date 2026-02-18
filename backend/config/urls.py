"""
Main URL configuration for FubaPay backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


# ---------------------------------------------
# Simple health check (important for production)
# ---------------------------------------------
def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "FubaPay Backend",
        "debug": settings.DEBUG
    })


urlpatterns = [

    # Admin panel
    path("admin/", admin.site.urls),

    # Health check endpoint
    path("health/", health_check, name="health_check"),

    # API v1
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/wallets/", include("apps.wallets.urls")),
    path("api/transactions/", include("apps.transactions.urls")),
    path("api/agents/", include("apps.agents.urls")),
    path("api/merchants/", include("apps.merchants.urls")),

]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)