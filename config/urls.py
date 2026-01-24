from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('salons.api_urls')),
    path('', include('accounts.urls')),
    path('', include('pages.urls')),
    path('', include('client.urls')),
    path('', include('salon_admin.urls')),
    path('', include('appointments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
