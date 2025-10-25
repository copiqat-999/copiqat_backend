from django.urls import path
from .views import (
    
    VaultDetailView,
    DepositCreateView,
    DepositListView,
    KYCVerificationView,
    DashboardView, 
    CreateTradeView,
    UserTradesView,
    CloseTradeView,
    TraderListView
)

urlpatterns = [
    path("trade/", CreateTradeView.as_view(), name="trade-create"),
    path('traders/', TraderListView.as_view(), name='trader-list'),
    path("list_trade", UserTradesView.as_view(), name="list-trades"),
    path("trades/<int:trade_id>/close/", CloseTradeView.as_view(), name="close-trade"),
    # path("my-trades/", UserTradeListView.as_view(), name="trade-create"),
    path("vault/", VaultDetailView.as_view(), name="vault-detail"),
    path("deposit/", DepositCreateView.as_view(), name="deposit-create"),
    path("deposits/", DepositListView.as_view(), name="deposit-list"),
    path('kyc/verify/', KYCVerificationView.as_view(), name='kyc-verify'),
    path("dashboard/", DashboardView.as_view(), name="user-dashboard"),
    
]

