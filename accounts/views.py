from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from .serializers import (
    UserRegisterSerializer,
    OTPVerificationSerializer,
    OTPRequestSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    LogoutSerializer,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import pyotp
from django.core.mail import send_mail
from django.conf import settings
from .models import User, OTP, PasswordResetToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .throttles import (
    LoginThrottle,
    PasswordResetThrottle,
    RequestPasswordResetThrottle,
    OTPRequestThrottle,
    OTPVerifyThrottle,
)

from .tasks import send_activation_email_task, send_password_reset_email_task, send_otp_reset_email_task

# Create your views here.


class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
        )
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            #  Generate OTP secret + code
            otp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(otp_secret, interval=600)
            otp_code = totp.now()

            #  Save OTP record
            OTP.objects.filter(user=user, is_verified=False).delete()  # Clear any old
            OTP.objects.create(user=user, otp_secret=otp_secret)

            try:
                send_activation_email_task.delay(user.id, otp_secret)

            except Exception as e:
                return Response(
                    {"error": f"Failed to send email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "data": serializer.data,
                    "message": f"Hi {user.first_name}, your account was created. An OTP has been sent to your email for verification.",
                },
                status=status.HTTP_201_CREATED,
            )


# View for Verifying email OTP (activate account)
class VerifyOTPView(GenericAPIView):
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp_code = str(serializer.validated_data["otp"]).strip()

            try:
                user = User.objects.get(email=email)
                if user.is_verified:
                    return Response(
                        {"error": "OTP is invalid, user is already verified"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                otp = OTP.objects.filter(user=user, is_verified=False).last()

            except OTP.DoesNotExist:
                return Response(
                    {"error": "No valid OTP found"}, status=status.HTTP_400_BAD_REQUEST
                )

            if otp.is_expired():
                return Response(
                    {"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Verify OTP and update the user
            totp = pyotp.TOTP(otp.otp_secret, interval=600)
            if totp.verify(otp_code, valid_window=1):
                otp.is_verified = True
                otp.save()
                user.is_verified = True
                user.is_active = True
                user.save()
                return Response(
                    {"message": "OTP verified successfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# View for Logout
class LogoutView(GenericAPIView):

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        user = request.user
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data["refresh"]
                token = RefreshToken(refresh_token)
                token.blacklist()  # Blacklist the refresh token
                # Make the user to be inactive
                user.is_active = False
                return Response(
                    {"message": "Successfully logged out"}, status=status.HTTP_200_OK
                )
            except TokenError as e:
                return Response(
                    {"error": f"Invalid token: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {"error": f"Logout failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(GenericAPIView):
    throttle_classes = [RequestPasswordResetThrottle]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST
                )

            #  Generate OTP secret + code
            otp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(otp_secret, interval=600)
            otp_code = totp.now()

            #  Save OTP record
            PasswordResetToken.objects.filter(
                user=user, is_verified=False
            ).delete()  # Clear any old
            PasswordResetToken.objects.create(user=user, otp_secret=otp_secret)

            #  Send the OTP via email

            try:
                send_password_reset_email_task(user.id, otp_secret)
            except Exception as e:
                return Response(
                    {"error": f"Failed to send email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response({"message": "verify your email to complete password reset"})


# View for Password Reset Confirmation
class PasswordResetConfirmView(GenericAPIView):
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp_code = str(serializer.validated_data["otp"]).strip()
            new_password = serializer.validated_data["new_password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                otp = PasswordResetToken.objects.filter(
                    user=user, is_verified=False
                ).latest("created_at")
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "No valid OTP found"}, status=status.HTTP_400_BAD_REQUEST
                )

            if otp.is_expired():
                return Response(
                    {"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Verify OTP
            totp = pyotp.TOTP(otp.otp_secret, interval=600)
            if totp.verify(otp_code):
                otp.is_verified = True
                otp.save()
                # Update password
                user.set_password(new_password)
                user.save()
                return Response(
                    {"message": "Password reset successfull"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




# View for requesting email verfication otp for account activation
class RequestOTPView(GenericAPIView):
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]

            # get the user
            try:
                user = User.objects.get(email=email)
                if user.is_verified:
                    return Response(
                        {"error": "OTP is invalid, user is already verified"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # create otp for the user

            #  Generate OTP secret + code
            otp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(otp_secret, interval=600)
            otp_code = totp.now()

            #  Save OTP record
            OTP.objects.filter(user=user, is_verified=False).delete()  # Clear any old
            OTP.objects.create(user=user, otp_secret=otp_secret)

            #  Send the OTP via email
            

            try:
                send_otp_reset_email_task(user.id, otp_secret)
            except Exception as e:
                return Response(
                    {"error": f"Failed to send email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "data": serializer.data,
                    "message": f"Hi {user.first_name}, your account was created. An OTP has been sent to your email for verification.",
                },
                status=status.HTTP_201_CREATED,
            )
