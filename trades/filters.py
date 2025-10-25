import django_filters
from .models import BuyAndSell


class TradeFilter(django_filters.FilterSet):
    class Meta:
        model = BuyAndSell
        fields = {"trade_status": ["iexact"]}
