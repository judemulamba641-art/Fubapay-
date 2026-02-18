from django.urls import path
from .views import (
    CreateMerchantProfileView,
    MerchantProfileView,
    UpdateMerchantSettingsView,
    MerchantDashboardView,
    AddMerchantWalletView,
    MerchantWalletListView,
)

urlpatterns = [
    path("create/", CreateMerchantProfileView.as_view()),
    path("profile/", MerchantProfileView.as_view()),
    path("update/", UpdateMerchantSettingsView.as_view()),
    path("dashboard/", MerchantDashboardView.as_view()),
    path("wallet/add/", AddMerchantWalletView.as_view()),
    path("wallets/", MerchantWalletListView.as_view()),
]