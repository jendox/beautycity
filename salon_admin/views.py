from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class SalonAdminView(LoginRequiredMixin, TemplateView):
    template_name = 'admin.html'
