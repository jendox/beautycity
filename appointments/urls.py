from django.urls import path

from . import views

urlpatterns = [
    path("service/", views.ServiceView.as_view(), name="service"),
    path("service/confirm/", views.ServiceConfirmView.as_view(), name="service_confirm"),
]
