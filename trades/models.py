from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BuyAndSell(models.Model):
    BUY = "buy"
    SELL = "sell"

    OPEN = "open"
    CLOSED = "closed"

    TRADE_STATUS = [
        (OPEN, "Open"),
        (CLOSED, "Closed"),
    ]

    TRADE_TYPE_CHOICES = [
        (BUY, "Buy"),
        (SELL, "Sell"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trades")
    asset = models.CharField(max_length=100)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES)
    trade_status = models.CharField(max_length=6, choices=TRADE_STATUS, default=OPEN)
    entry_price = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    take_profit = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    stop_loss = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)

    duration = models.CharField(max_length=20)
    pl = models.DecimalField(  # profit/loss
        max_digits=12, decimal_places=4, default=0.00, verbose_name="Profit/Loss"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name} - {self.asset.upper()} - {self.trade_type.upper()}"
    


class Asset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('crypto', 'Crypto'),
        ('forex', 'Forex'),
        ('stock', 'Stock'),
    ]

    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, unique=True)  # e.g., "BTC/USD", "AAPL"
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPE_CHOICES)
    current_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Vault(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vault")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    earning = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    today = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    daily_pl = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    weekly_pl = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_pl = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name}'s Vault - Balance: {self.balance}"


class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deposits")
    # amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    receipt = models.ImageField(upload_to="receipts/")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deposit by {self.user} - Receipt uploaded"


class Trader(models.Model):
    stars = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=255)
    returns = models.DecimalField(max_digits=5, decimal_places=2)  # percentage
    win_rate = models.DecimalField(max_digits=5, decimal_places=2) # percentage
    copiers = models.PositiveIntegerField()

    def __str__(self):
        return self.name