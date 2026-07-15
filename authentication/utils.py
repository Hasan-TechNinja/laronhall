import os
import random
from twilio.rest import Client
from dotenv import load_dotenv
from authentication.models import RegisterOTP, ForgotPasswordOTP

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID') or os.getenv('SERVICE_SID', '')

client = Client(account_sid, auth_token)

def normalize_phone_number(phone):
    """
    Normalizes phone numbers to E.164 format.
    If phone starts with '01' and is 11 digits, prepends '+88'.
    If phone starts with '880' and is 13 digits, prepends '+'.
    """
    if not phone:
        return ""
    # Remove any spaces, dashes or parentheses
    phone = "".join(c for c in phone if c.isdigit() or c == "+")
    if phone.startswith("01") and len(phone) == 11:
        phone = "+88" + phone
    elif phone.startswith("880") and len(phone) == 13:
        phone = "+" + phone
    elif phone.startswith("1") and len(phone) == 10:
        phone = "+1" + phone
    return phone


def send_otp_phone(phone_number):
    """Send OTP to a phone number."""
    normalized_phone = normalize_phone_number(phone_number)
    verification = client.verify.services(
        TWILIO_VERIFY_SERVICE_SID
    ).verifications.create(
        to=normalized_phone,
        channel="sms"
    )
    print("OTP sent, Verification SID:", verification.sid)
    return verification.sid


def verify_otp(phone_number, otp_string):
    """Validate OTP and consume it if still valid."""
    normalized_phone = normalize_phone_number(phone_number)
    verification_check = client.verify.services(
        TWILIO_VERIFY_SERVICE_SID
    ).verification_checks.create(
        to=normalized_phone,
        code=otp_string
    )
    print("Verification status:", verification_check.status)
    return verification_check.status == "approved"


def create_reset_secret(user):
    secret = random.randint(100000, 999999)
    ForgotPasswordOTP.objects.filter(user=user).delete()
    ForgotPasswordOTP.objects.create(user=user, otp=str(secret))
    return secret
