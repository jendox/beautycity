
from django.views.generic import TemplateView


class ServiceView(TemplateView):
    template_name = "service.html"


class ServiceConfirmView(TemplateView):
    template_name = "service_finally.html"
