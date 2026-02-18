from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    GoogleLoginView,
    ProfileView,
    UpdateProfileView,
    AdminUserListView,
    AdminRoleUpdateView,
)

urlpatterns = [

    # =====================================================
    # AUTHENTICATION
    # =====================================================

    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # =====================================================
    # USER PROFILE
    # =====================================================

    path("me/", ProfileView.as_view(), name="profile"),
    path("me/update/", UpdateProfileView.as_view(), name="update_profile"),

    # =====================================================
    # ADMIN MANAGEMENT
    # =====================================================

    path("admin/users/", AdminUserListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:user_id>/role/",
         AdminRoleUpdateView.as_view(),
         name="admin_update_role"),

]