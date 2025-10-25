from django.contrib import admin

# Register your models here.
from django.contrib.admin import register
from django.contrib import admin
from django.contrib.auth import get_user_model
from unfold.admin import ModelAdmin
from unfold.forms import AdminOwnPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    model = User
    list_display = (
        "email",
        "full_name",
        "is_active",
        "is_verified",
        "is_KYC_verified",
        "is_staff",
        "is_superuser",
        "referral_code",
        "referral_count",
        "date_joined",
    )
    readonly_fields = ("date_joined", "last_login", "referral_code", "referral_count")
    ordering = ("-date_joined",)
    search_fields = ("email", "first_name", "last_name", "referral_code")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        (
            "Referral Info",
            {"fields": ("referral_code", "referred_by", "referral_count")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_verified",
                    "is_KYC_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
