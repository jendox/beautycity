from django.urls import path

from salons import api_views

urlpatterns = [
    path("salons/", api_views.SalonListAPIView.as_view(), name="api_salons"),
    path("salons/<int:salon_id>/services/", api_views.SalonServicesAPIView.as_view(), name="api_salon_services"),
    path("salons/<int:salon_id>/masters/", api_views.SalonMastersAPIView.as_view(), name="api_salon_masters"),
    path("masters/", api_views.MasterListAPIView.as_view(), name="api_masters"),
    path("masters/<int:master_id>/", api_views.MasterDetailAPIView.as_view(), name="api_master_detail"),
    path("services/<int:service_id>/", api_views.ServiceDetailAPIView.as_view(), name="api_service_detail"),
]
