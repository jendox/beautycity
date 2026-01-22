from django.shortcuts import render
from django.urls import path

urlpatterns = [
    path('', render, kwargs={'template_name': 'index.html'}, name='index'),
]
