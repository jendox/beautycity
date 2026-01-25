from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from salons.models import SalonAdmin


@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser:
        return HttpResponseRedirect("/admin/")
    if SalonAdmin.objects.filter(user=user, is_active=True).exists():
        return HttpResponseRedirect(reverse("salon_admin"))
    return HttpResponseRedirect(reverse("client_cabinet"))
