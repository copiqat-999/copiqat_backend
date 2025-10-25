from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import BuyAndSell, Vault, Deposit, Asset, Trader
from django.utils.html import format_html


@admin.register(BuyAndSell)
class BuyAndSellAdmin(ModelAdmin):
    list_display = ("user", "asset", "trade_type", "trade_status", "entry_price", "pl", "duration")
    list_filter = ("trade_type", "trade_status", "created_at")
    search_fields = ("user__username", "asset")
    ordering = ("-created_at",)

    fieldsets = (
        ("Trade Information", {
            "fields": ("user", "asset", "trade_type", "trade_status", "entry_price", "pl")
        }),
        ("Meta", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at",)


@admin.register(Vault)
class VaultAdmin(ModelAdmin):
    list_display = ("user", "balance", "daily_pl", "weekly_pl", "earning", "monthly_pl", "updated_at", "today")
    search_fields = ("user__username", "user__email")
    ordering = ("-updated_at",)

    fieldsets = (
        ("User Vault Info", {
            "fields": ("user", "balance", "daily_pl", "weekly_pl", "monthly_pl", "earning")
        }),
        ("Timestamps", {
            "fields": ("updated_at",),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("updated_at",)


@admin.register(Deposit)
class DepositAdmin(ModelAdmin):
    list_display = ("user", "receipt_preview", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user__username",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("user", "receipt", "receipt_preview", "is_approved")
        }),
        ("Meta", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("receipt_preview", "created_at")

    def receipt_preview(self, obj):
        if obj.receipt:
            return format_html('<img src="{}" style="max-height: 200px;"/>', obj.receipt.url)
        return "No preview"
    receipt_preview.short_description = "Receipt Preview"



@admin.register(Asset)
class AssetAdmin(ModelAdmin):
    list_display = ("symbol", "name", "asset_type", "current_price", "last_updated")
    list_filter = ("asset_type",)
    search_fields = ("symbol", "name")
    ordering = ("symbol",)
    readonly_fields = ("last_updated",)

    fieldsets = (
        (None, {
            "fields": ("symbol", "name", "asset_type", "current_price", "last_updated"),
        }),
    )


@admin.register(Trader)
class TraderAdmin(ModelAdmin):
    list_display = ("name", "stars", "returns", "win_rate", "copiers")
    search_fields = ("name",)
    list_filter = ("stars",)
    ordering = ("-win_rate",)  # default ordering in admin