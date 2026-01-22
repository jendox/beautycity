from rest_framework import serializers

from accounts.phone import normalize_phone


class RequestCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_phone(value)
        except ValueError:
            raise serializers.ValidationError("invalid_phone")


class ValidateCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=4)

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_phone(value)
        except ValueError:
            raise serializers.ValidationError("invalid_phone")
