from django.urls import path

from . import api_views

urlpatterns = [
    path('api/auth/csrf/', api_views.csrf, name='api_csrf'),
    path('api/auth/request-code/', api_views.RequestCodeAPIView.as_view(), name='api_request_code'),
    path('api/auth/verify-code/', api_views.VerifyCodeAPIView.as_view(), name='api_verify_code'),
    path('/api/auth/logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
]
