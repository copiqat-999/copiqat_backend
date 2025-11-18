from rest_framework import generics, permissions
from .models import BuyAndSell, Vault, Deposit, Asset
from django.core.cache import cache
from .serializers import TradeSerializer, VaultSerializer, DepositSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView
from rest_framework import status
from .serializers import DashboardSerializer
from decimal import Decimal, InvalidOperation
from django.conf import settings
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .filters import TradeFilter
from django_redis import get_redis_connection
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Trader
from .serializers import TraderSerializer


def clear_user_trade_cache(user_id):
    """
    Deletes both open and closed trade caches for a specific user.
    """
    cache_keys = [
        f"user_trades_{user_id}_trade_status__iexact=open",
        f"user_trades_{user_id}_trade_status__iexact=closed",
    ]
    for key in cache_keys:
        cache.delete(key)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []  # 🚫 disable throttling just for this view

    def get(self, request):
        user = request.user
        vault = getattr(user, "vault", None)

        data = {
            "balance": vault.balance if vault else 0.00,
            "earning": vault.earning if vault else 0.00,
            "daily_pl": vault.daily_pl if vault else 0.00,
            "today": vault.today if vault else 0.00,
            "weekly_pl": vault.weekly_pl if vault else 0.00,
            "monthly_pl": vault.monthly_pl if vault else 0.00,
            "active_trades_count": BuyAndSell.objects.filter(
                user=user, trade_status="open"
            ).count(),
            "referral_count": user.referral_count,
            "referral_link": f"https://www.copiqat.trade/auth/signup?ref={user.referral_code}",
        }

        serializer = DashboardSerializer(data)  # ✅ correct usage
        return Response(serializer.data)


CACHE_TTL = 55  # seconds


class UserTradesView(APIView):
    """Return the user's trades with PL & PL% calculations."""

    throttle_classes = []  # 🚫 disable throttling just for this view
    filterset_class = TradeFilter

    def get(self, request, *args, **kwargs):
        user_id = request.user.id

        # ✅ Include query params in cache key to support filtering
        filter_param = request.GET.urlencode() or "all"
        cache_key = f"user_trades_{user_id}_{filter_param}"

        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        trades = BuyAndSell.objects.filter(user=request.user).select_related()

        # ✅ Apply filtering
        filterset = TradeFilter(request.GET, queryset=trades)
        trades = filterset.qs

        trade_list = []
        for trade in trades:
            try:
                asset_obj = Asset.objects.get(symbol=trade.asset)
                current_price = asset_obj.current_price
            except Asset.DoesNotExist:
                current_price = trade.entry_price  # fallback if Asset missing

            # Calculate PL
            if trade.trade_type == BuyAndSell.BUY:
                pl_value = current_price - trade.entry_price
            else:  # SELL
                pl_value = trade.entry_price - current_price

            # Calculate PL%
            try:
                pl_percent = (pl_value / trade.entry_price) * 100
            except (ZeroDivisionError, InvalidOperation):
                pl_percent = Decimal("0.00")

            trade_list.append(
                {
                    "id": trade.id,
                    "asset": trade.asset,
                    "trade_type": trade.trade_type,
                    "trade_status": trade.trade_status,
                    "entry_price": str(trade.entry_price),
                    "current_price": str(current_price),
                    "pl": str(round(pl_value, 2)),
                    "pl_percent": str(round(pl_percent, 2)),
                    "duration": trade.duration,
                    "created_at": trade.created_at,
                }
            )

        # Cache per user+filter combo
        cache.set(cache_key, trade_list, CACHE_TTL)
        return Response(trade_list)


class CreateTradeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TradeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        asset_symbol = serializer.validated_data["asset"]
        trade_type = serializer.validated_data["trade_type"]
        duration = serializer.validated_data["duration"]

        # Get asset from DB
        asset_obj = get_object_or_404(Asset, symbol=asset_symbol)

        # Create trade with entry_price = current_price at the time
        trade = BuyAndSell.objects.create(
            user=request.user,
            asset=asset_symbol,
            trade_type=trade_type,
            duration=duration,
            entry_price=asset_obj.current_price,
        )

        return Response(
            TradeSerializer(trade, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CloseTradeView(APIView):
    def post(self, request, trade_id):
        # Get trade belonging to the user
        trade = get_object_or_404(BuyAndSell, id=trade_id, user=request.user)

        if trade.trade_status == "closed":
            return Response(
                {"detail": "Trade already closed."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update status to closed
        trade.trade_status = "closed"
        trade.save()

        # Invalidate cache
        # clear_user_trade_cache(request.user.id)

        return Response(
            {"detail": "Trade closed successfully."}, status=status.HTTP_200_OK
        )


class VaultDetailView(generics.RetrieveAPIView):
    """
    Returns the authenticated user's vault
    """

    serializer_class = VaultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.vault


class DepositCreateView(generics.CreateAPIView):
    """
    Allows a user to submit deposit proof
    """

    serializer_class = DepositSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DepositListView(generics.ListAPIView):
    """
    Allows admin/staff to view all deposits
    """

    queryset = Deposit.objects.all().order_by("-created_at")
    serializer_class = DepositSerializer
    permission_classes = [permissions.IsAdminUser]


class KYCVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_KYC_verified = True
        user.save()
        return Response(
            {"message": "KYC verification completed."}, status=status.HTTP_200_OK
        )


class TraderListView(generics.ListAPIView):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["stars"]  # filter by stars
    search_fields = ["name"]  # search by name
    ordering_fields = ["win_rate", "returns", "copiers"]  # sort by these fields
    ordering = ["-win_rate", "-returns", "-copiers"]

