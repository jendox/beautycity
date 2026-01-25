from __future__ import annotations

from datetime import date

from django.utils import timezone
from rest_framework import serializers

from accounts.phone import normalize_phone
from appointments.models import PromoCode


class AvailabilityDatesQuerySerializer(serializers.Serializer):
    from_ = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    to = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    salon_id = serializers.IntegerField(required=False)
    master_id = serializers.IntegerField(required=False)
    service_id = serializers.IntegerField(required=True)

    def to_internal_value(self, data):
        if data is not None and "from" in data and "from_" not in data:
            copied = data.copy()
            copied["from_"] = data.get("from")
            data = copied
        return super().to_internal_value(data)

    def validate(self, attrs):
        from_date: date = attrs["from_"]
        to_date: date = attrs["to"]
        if to_date < from_date:
            raise serializers.ValidationError({"detail": "invalid_request"})

        if not attrs.get("salon_id") and not attrs.get("master_id"):
            raise serializers.ValidationError({"detail": "missing_params"})
        return attrs


class AvailabilitySlotsQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    salon_id = serializers.IntegerField(required=False)
    master_id = serializers.IntegerField(required=False)
    service_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        if not attrs.get("salon_id") and not attrs.get("master_id"):
            raise serializers.ValidationError({"detail": "missing_params"})
        return attrs


class MasterAvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    service_id = serializers.IntegerField(required=True)


class CreateHoldSerializer(serializers.Serializer):
    salon_id = serializers.IntegerField(required=True)
    service_id = serializers.IntegerField(required=True)
    master_id = serializers.IntegerField(required=False, allow_null=True)
    starts_at = serializers.DateTimeField(required=True)
    promo_code = serializers.CharField(required=False, allow_blank=True)


class ApplyPromoSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=True, allow_blank=False)


class ConfirmAppointmentSerializer(serializers.Serializer):
    hold_id = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    pd_consent = serializers.BooleanField(required=False, default=True)

    def validate_hold_id(self, value: str) -> str:
        value = (value or "").strip()
        if value.startswith("hld_"):
            return value[4:]
        return value

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_phone(value)
        except ValueError:
            raise serializers.ValidationError("invalid_phone") from None


def get_active_promo_by_code(code: str, now: timezone.datetime | None = None) -> PromoCode | None:
    if not code:
        return None
    code = code.strip()
    if not code:
        return None
    promo = PromoCode.objects.filter(code__iexact=code).first()
    if not promo:
        return None
    if not promo.is_valid_at(now=now or timezone.now()):
        return None
    return promo
