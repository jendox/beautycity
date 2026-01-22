from django.urls import path

from . import api_views

urlpatterns = [
    path('api/auth/csrf', api_views.csrf, name='api_csrf'),
    path('api/auth/request-otp', api_views.RequestCodeAPIView.as_view(), name='api_request_otp'),
    path('api/auth/verify-otp', api_views.VerifyCodeAPIView.as_view(), name='api_verify_otp'),
]
