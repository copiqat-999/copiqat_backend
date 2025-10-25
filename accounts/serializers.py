from rest_framework import serializers
from .models import User, PasswordResetToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
import pyotp


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=8, write_only=True)
    referral_code = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "referral_code",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    def validate_referral_code(self, value):
        if value:
            if not User.objects.filter(referral_code=value).exists():
                raise serializers.ValidationError("Invalid referral code.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")

        # Pop the referral_code to prevent it from being passed to create_user
        referral_code = validated_data.pop("referral_code", None)
        referred_by = None

        if referral_code:
            try:
                referred_by = User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid referral code.")

        user = User.objects.create_user(**validated_data)

        if referred_by:
            user.referred_by = referred_by
            user.save()

        return user


# Serializer for OTP Verification
class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    kyc_verified = serializers.BooleanField(read_only=True)
    referral_code = serializers.CharField(read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "password", "kyc_verified", "referral_code", "access_token", "refresh_token"]

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        request = self.context.get("request")
        user = authenticate(request, email=email, password=password)

        if not user:
            raise AuthenticationFailed("invalid credentials, please try again")

        if not user.is_verified:
            raise AuthenticationFailed("Email is not verified")

        user_token = user.tokens()

        return {
            "email": user.email,
            "full_name": user.get_full_name,
            "kyc_verified" : user.is_KYC_verified,
            "referral_code" : user.referral_code,
            "access_token": str(user_token.get("access")),
            "refresh_token": str(user_token.get("refresh")),
        }


# Serializer for Logout
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# Serializer for Password Reset Confirmation
class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data
