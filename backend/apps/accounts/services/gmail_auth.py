"""
Gmail OAuth authentication service for FubaPay
"""

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# =====================================================
# VERIFY GOOGLE TOKEN
# =====================================================

def verify_google_token(id_token: str):
    """
    Verify Google ID token and return user info
    """
    google_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"

    response = requests.get(google_url)

    if response.status_code != 200:
        raise Exception("Invalid Google token")

    data = response.json()

    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise Exception("Token audience mismatch")

    return {
        "email": data.get("email"),
        "google_id": data.get("sub"),
        "email_verified": data.get("email_verified"),
        "full_name": data.get("name"),
        "picture": data.get("picture"),
    }


# =====================================================
# GET OR CREATE USER
# =====================================================

def get_or_create_user(user_data: dict):
    """
    Create user if not exists
    """

    user, created = User.objects.get_or_create(
        email=user_data["email"],
        defaults={
            "google_id": user_data["google_id"],
            "full_name": user_data.get("full_name", ""),
            "is_active": True,
        }
    )

    # Update google_id if missing
    if not user.google_id:
        user.google_id = user_data["google_id"]
        user.save()

    return user


# =====================================================
# GENERATE JWT TOKENS
# =====================================================

def generate_jwt_tokens(user):
    """
    Generate access and refresh tokens
    """

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# =====================================================
# MAIN AUTH FUNCTION
# =====================================================

def authenticate_with_google(id_token: str):
    """
    Full authentication flow:
    1. Verify token
    2. Get or create user
    3. Generate JWT
    """

    user_data = verify_google_token(id_token)

    if not user_data["email_verified"]:
        raise Exception("Google email not verified")

    user = get_or_create_user(user_data)

    tokens = generate_jwt_tokens(user)

    return {
        "user_id": user.id,
        "email": user.email,
        "tokens": tokens,
    }