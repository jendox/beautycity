from rest_framework import serializers

from salons.models import Master, Salon, Service


class SalonSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Salon
        fields = ("id", "name", "address", "image_url")

    def get_image_url(self, obj: Salon) -> str | None:
        if not obj.image:
            return None
        return obj.image.url


class ServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ("id", "title", "price", "duration_minutes", "image_url")

    def get_image_url(self, obj: Service) -> str | None:
        if not obj.image:
            return None
        return obj.image.url


class MasterSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Master
        fields = ("id", "name", "image_url")

    def get_image_url(self, obj: Master) -> str | None:
        if not getattr(obj, "image", None):
            return None
        if not obj.image:
            return None
        return obj.image.url
