from django.urls import path
from .views import (
    AgentProfileView,
    AgentLimitsView,
    CheckTransactionPermissionView,
    RecalculateScoreView,
    FreezeAgentView
)

urlpatterns = [
    path("profile/", AgentProfileView.as_view()),
    path("limits/", AgentLimitsView.as_view()),
    path("check-transaction/", CheckTransactionPermissionView.as_view()),
    path("recalculate/<int:agent_id>/", RecalculateScoreView.as_view()),
    path("freeze/<int:agent_id>/", FreezeAgentView.as_view()),
]