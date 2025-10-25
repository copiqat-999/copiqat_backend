import random
import string
from django.conf import settings
from django.core.mail import send_mail


def generate_referral_code():
    from .models import User  # Import here to avoid circular imports

    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not User.objects.filter(referral_code=code).exists():
            return code


def send_activation_email(user, otp_code):
    subject = "Your OTP Code for account activation"
    message = f"Hi {user.first_name},\n\nActivate your account by verifying your email with this OTP {otp_code}. It is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


def send_otp_reset_email(user, otp_code):
    subject = "Your OTP Code for account activation"
    message = f"Hi {user.first_name},\n\nActivate your account by verifying your email with this OTP {otp_code}. It is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)



def send_password_reset_email(user, otp_code):
    subject = "Your OTP Code for password reset"
    message = f"Hi {user.first_name},\n\nFinish the password reset process by verifying your email with this OTP {otp_code}. It is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)
