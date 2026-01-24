from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from salons.models import Master, Salon, Service, ServiceCategory
from salons.serializers import MasterSerializer, SalonSerializer, ServiceSerializer


class SalonListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        salons = Salon.objects.all().order_by("id")
        return Response(data={"results": SalonSerializer(salons, many=True).data})


class SalonServicesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, salon_id: int):
        salon = get_object_or_404(Salon, pk=salon_id)

        categories = (
            ServiceCategory.objects.filter(salon=salon, is_active=True)
            .order_by("sort_order", "id")
            .prefetch_related("services")
        )
        services = Service.objects.filter(salon=salon, is_active=True).select_related("category").order_by("id")

        services_by_category_id: dict[int, list[Service]] = {}
        uncategorized: list[Service] = []
        for service in services:
            if service.category_id is None:
                uncategorized.append(service)
                continue
            services_by_category_id.setdefault(service.category_id, []).append(service)

        return Response(
            data={
                "salon": {"id": salon.id, "name": salon.name},
                "categories": [
                    {
                        "id": category.id,
                        "title": category.title,
                        "services": ServiceSerializer(services_by_category_id.get(category.id, []), many=True).data,
                    }
                    for category in categories
                ],
                "uncategorized": ServiceSerializer(uncategorized, many=True).data,
            },
        )


class SalonMastersAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, salon_id: int):
        salon = get_object_or_404(Salon, pk=salon_id)
        masters = Master.objects.filter(salon=salon, is_active=True).order_by("id")
        return Response(data={"results": MasterSerializer(masters, many=True).data})


class MasterListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        masters = Master.objects.filter(is_active=True).select_related("salon").order_by("id")
        payload = []
        for master in masters:
            payload.append(
                {
                    **MasterSerializer(master).data,
                    "primary_salon": {"id": master.salon_id, "name": master.salon.name},
                },
            )
        return Response(data={"results": payload})


class MasterDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, master_id: int):
        master = get_object_or_404(Master, pk=master_id)
        return Response(
            data={
                **MasterSerializer(master).data,
                "salon": {"id": master.salon_id, "name": master.salon.name, "address": master.salon.address},
            },
        )


class ServiceDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, service_id: int):
        service = get_object_or_404(Service.objects.select_related("salon", "category"), pk=service_id)
        data = {
            **ServiceSerializer(service).data,
            "salon": {"id": service.salon_id, "name": service.salon.name, "address": service.salon.address},
            "category": {"id": service.category_id, "title": service.category.title} if service.category else None,
        }
        return Response(data=data)
