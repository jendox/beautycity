import random
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PersonalDataConsent, PhoneOTP
from accounts.otp_delivery import deliver_otp
from accounts.phone import normalize_phone, phone_to_user_field
from accounts.serializers import PersonalDataConsentSerializer, RequestCodeSerializer, ValidateCodeSerializer
from config import settings
from salons.models import SalonAdmin

User = get_user_model()


def _generate_code() -> str:
    return f"{random.randint(0, 9999):04d}"


def _get_dashboard_url(user: User) -> str:
    if user.is_superuser:
        return "/admin"
    if SalonAdmin.objects.filter(user=user, is_active=True).exists():
        return reverse("salon_admin")
    return reverse("client_cabinet")


@require_GET
def csrf(request):
    token = get_token(request)
    return JsonResponse({"csrfToken": token})


@require_GET
def consent_required(request):
    raw_phone = request.GET.get("phone", "")
    try:
        phone_e164 = normalize_phone(raw_phone)
    except ValueError:
        return JsonResponse({"detail": "invalid_phone"}, status=400)

    if User.objects.filter(phone=phone_to_user_field(phone_e164)).exists():
        return JsonResponse({"required": False})
    if PersonalDataConsent.objects.filter(phone=phone_e164).exists():
        return JsonResponse({"required": False})
    return JsonResponse({"required": True})


class PersonalDataConsentAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PersonalDataConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_e164 = serializer.validated_data["phone"]
        PersonalDataConsent.objects.get_or_create(phone=phone_e164)

        return Response(data={"ok": True})


class RequestCodeAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RequestCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_e164 = serializer.validated_data["phone"]
        resend_timeout = getattr(settings, "OTP_RESEND_TIMEOUT_SECONDS", 60)
        recent = PhoneOTP.objects.filter(
            phone=phone_e164,
            created_at__gte=timezone.now() - timedelta(seconds=resend_timeout),
        ).exists()
        if recent:
            return Response(
                data={"detail": "try_later", "timeout_seconds": resend_timeout},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        code = _generate_code()
        otp_ttl = getattr(settings, "OTP_TTL_SECONDS", 300)
        PhoneOTP.create_otp(phone_e164, code, otp_ttl)
        deliver_otp(phone_e164, code)

        request.session["auth_phone_pending"] = phone_e164

        return Response(data={"ok": True, "ttl_seconds": otp_ttl})


class VerifyCodeAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ValidateCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_e164 = serializer.validated_data["phone"]
        code = serializer.validated_data["code"].strip()
        pending = request.session.get("auth_phone_pending")
        if pending and pending != phone_e164:
            return Response(
                data={"detail": "phone_mismatch"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = authenticate(request, phone_e164=phone_e164, code=code)
        except Exception as exc:
            if hasattr(exc, "status_code") and hasattr(exc, "detail"):
                return Response(data=exc.detail, status=exc.status_code)
            raise

        login(request, user)
        request.session.pop("auth_phone_pending", None)

        # Link existing guest appointments (created by phone) to the newly logged-in user.
        try:
            from appointments.models import Appointment

            Appointment.objects.filter(user__isnull=True, client_phone=phone_e164).update(user=user)
        except Exception:
            pass

        return Response(
            data={
                "ok": True,
                "next_url": _get_dashboard_url(user),
                "user": {
                    "id": user.id,
                    "phone": str(user.phone),
                    "display_name": user.display_name,
                    "is_superuser": user.is_superuser,
                },
            },
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        request.session.pop("auth_phone_pending", None)
        return Response(data={"ok": True})
