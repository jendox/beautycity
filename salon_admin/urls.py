from django.urls import path

from . import views

urlpatterns = [
    path('salon-admin/', views.SalonAdminView.as_view(), name='salon_admin'),
]
