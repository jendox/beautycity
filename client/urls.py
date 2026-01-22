from django.urls import path

from . import views

urlpatterns = [
    path('cabinet/', views.CabinetView.as_view(), name='client_cabinet'),
]