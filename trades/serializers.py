from rest_framework import serializers
from .models import BuyAndSell, Vault, Deposit, Trader


class TradeSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(
        max_digits=20, decimal_places=8, read_only=True
    )
    pl = serializers.DecimalField(max_digits=20, decimal_places=8, read_only=True)
    pl_percent = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = BuyAndSell
        fields = [
            "id",
            "asset",
            "trade_type",
            "duration",
            "entry_price",
            "current_price",
            "take_profit",
            "stop_loss",
            "pl",
            "pl_percent",
            "trade_status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "pl",
            "pl_percent",
            "entry_price",
            "current_price",
            "trade_status",
        ]

    def validate(self, data):
        """
        Cross-field validation for trade logic.
        - Prevents duplicate active trades for the same asset and type.
        - Ensures user has sufficient balance in their vault before initiating a trade.
        """
        user = self.context["request"].user
        asset = data.get("asset")
        trade_type = data.get("trade_type")

        # Ensure the user's vault exists
        if not hasattr(user, "vault"):
            raise serializers.ValidationError(
                "Vault not found. Please contact support."
            )

        # Prevent initiating trades with negative wallet balance
        # if user.vault.balance <= 0:
        #     raise serializers.ValidationError(
        #         "Insufficient wallet balance. Please top up your wallet."
        #     )

        # Prevent duplicate open trades on same asset
        if BuyAndSell.objects.filter(
            user=user, asset=asset, trade_type=trade_type, trade_status="open"
        ).exists():
            raise serializers.ValidationError(
                f"You already have an open {trade_type.upper()} trade for {asset.upper()}."
            )
        return data


class VaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vault
        fields = [
            "id",
            "user",
            "balance",
            "daily_pl",
            "today",
            "weekly_pl",
            "monthly_pl",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value

    def validate_daily_pl(self, value):
        return self._validate_profit_loss(value, "Daily P/L")

    def validate_weekly_pl(self, value):
        return self._validate_profit_loss(value, "Weekly P/L")

    def validate_monthly_pl(self, value):
        return self._validate_profit_loss(value, "Monthly P/L")

    def _validate_profit_loss(self, value, label):
        # Accepting negative values (losses) is okay,
        # but you can restrict extreme values here if needed
        if abs(value) > 1_000_000:
            raise serializers.ValidationError(f"{label} is unrealistically large.")
        return value


class DepositSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.ImageField()

    class Meta:
        model = Deposit
        fields = ["id", "user", "receipt", "is_approved", "created_at"]
        read_only_fields = ["id", "is_approved", "created_at"]

    # def validate_amount(self, value):
    #     if value <= 0:
    #         raise serializers.ValidationError("Deposit amount must be greater than 0.")

    #     return value

    def validate_receipt(self, value):
        max_size = 2 * 1024 * 1024  # 2MB

        if not value.content_type.startswith("image/"):
            raise serializers.ValidationError("Receipt must be an image.")

        if value.size > max_size:
            raise serializers.ValidationError("Image size should not exceed 2MB.")

        return value


# serializers.py
class DashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    earning = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    weekly_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_trades_count = serializers.IntegerField()
    referral_count = serializers.IntegerField()
    referral_link = serializers.CharField()


class TraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = "__all__"
