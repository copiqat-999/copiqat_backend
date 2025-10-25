from celery import shared_task
from .models import User
import pyotp
from .utils import send_activation_email, send_password_reset_email, send_otp_reset_email

@shared_task
def send_activation_email_task(user_id, otp_secret):
    user = User.objects.get(id=user_id)
    otp_code = pyotp.TOTP(otp_secret, interval=600).now()
    send_activation_email(user=user, otp_code=otp_code)

@shared_task
def send_password_reset_email_task(user_id, otp_secret):
    user = User.objects.get(id=user_id)
    otp_code = pyotp.TOTP(otp_secret, interval=600).now()
    send_password_reset_email(user=user, otp_code=otp_code)

@shared_task
def send_otp_reset_email_task(user_id, otp_secret):
    user = User.objects.get(id=user_id)
    otp_code = pyotp.TOTP(otp_secret, interval=600).now()
    send_otp_reset_email(user=user, otp_code=otp_code)
