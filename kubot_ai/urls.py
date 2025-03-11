from django.urls import path
from .views import TelegramWebhookView
from .api_views import (
    TaskListCreateView, CompleteTaskView, RewardListView, ReferralView,
    WalletDetailView, WithdrawTokensView
)


urlpatterns = [
    path("telegram-webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    
    # API VIEWS
    path('api/tasks/', TaskListCreateView.as_view(), name="task-list-create"),
    path('api/tasks/complete/<int:user_id>/<int:task_id>/', CompleteTaskView.as_view(), name="complete-task"),
    path('api/rewards/', RewardListView.as_view(), name="reward-list"),
    path('api/referr/<str:referral_id>/', ReferralView.as_view(), name="referral"),
    path('api/wallet/<str:username>/', WalletDetailView.as_view(), name="wallet-detail"),
    path('api/wallet/withdraw/', WithdrawTokensView.as_view(), name="withdraw-tokens"),
]
