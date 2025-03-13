from django.urls import path
from .views import TelegramWebhookView
from .api_views import (
    TaskListCreateView, CompleteTaskView, RewardListView, ReferralRegisterView,
    WalletDetailView, WithdrawTokensView, FundTokensView, RegisterView, GetCompleteTaskView
)


urlpatterns = [
    path("telegram-webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    
    # API VIEWS
    path('/tasks/', TaskListCreateView.as_view(), name="task-list-create"),
    path('/tasks/complete/<int:user_id>/<int:task_id>/', CompleteTaskView.as_view(), name="complete-task"),
    path('/tasks/completed/<int:user_id>/', GetCompleteTaskView.as_view(), name="completed-task"),
    path('/rewards/<str:username>/', RewardListView.as_view(), name="reward-list"),
    path('/referr/<str:referral_id>/', ReferralRegisterView.as_view(), name="referral"),
    path('/wallet/create/', RegisterView.as_view(), name="referral"),
    path('/wallet/<str:username>/', WalletDetailView.as_view(), name="wallet-detail"),
    path('/wallet/withdraw/<str:username>/', WithdrawTokensView.as_view(), name="withdraw-tokens"),
    path('/wallet/fund/<str:username>/', FundTokensView.as_view(), name="fund")
]
