import random
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PhoneOTP
from accounts.otp_delivery import deliver_otp
from accounts.serializers import RequestCodeSerializer, ValidateCodeSerializer
from config import settings


def _generate_code() -> str:
    return f"{random.randint(0, 9999):04d}"


@require_GET
def csrf(request):
    token = get_token(request)
    return JsonResponse({"csrfToken": token})


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

        return Response(
            data={
                "ok": True,
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
