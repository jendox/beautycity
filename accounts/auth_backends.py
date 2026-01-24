from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import PersonalDataConsent, PhoneOTP
from accounts.phone import phone_to_user_field
from config import settings

User = get_user_model()


class OTPAuthError(AuthenticationFailed):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, code: str, status_code: int | None = None):
        detail = {"detail": code}
        super().__init__(detail=detail)
        if status_code is not None:
            self.status_code = status_code


def _check_otp(otp: PhoneOTP, code: str) -> tuple[str, int] | None:
    if not otp or otp.is_expired():
        return "code_expired", status.HTTP_400_BAD_REQUEST

    max_attempts = getattr(settings, "OTP_MAX_ATTEMPTS", 3)
    if otp.attempts >= max_attempts:
        return "too_many_attempts", status.HTTP_429_TOO_MANY_REQUESTS

    if not otp.check_code(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        return "invalid_code", status.HTTP_400_BAD_REQUEST

    return None


class PhoneOTPBackend(ModelBackend):
    def authenticate(self, request, phone_e164=None, code=None, **kwargs):
        if not phone_e164 or not code:
            return None

        otp = (PhoneOTP.objects
               .filter(phone=phone_e164, used_at__isnull=True)
               .order_by("-created_at")
               .first())

        result = _check_otp(otp, code)
        if result:
            error, status_code = result
            raise OTPAuthError(error, status_code)

        with transaction.atomic():
            otp.used_at = timezone.now()
            otp.save(update_fields=["used_at"])

            user, _created = User.objects.get_or_create(
                phone=phone_to_user_field(phone_e164),
                defaults={"username": ""},
            )
            PersonalDataConsent.objects.get_or_create(phone=phone_e164)

        if not self.user_can_authenticate(user):
            raise OTPAuthError("user_inactive", status.HTTP_403_FORBIDDEN)

        return user
