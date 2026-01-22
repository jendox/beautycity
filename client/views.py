from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class CabinetView(LoginRequiredMixin, TemplateView):
    template_name = 'notes.html'
