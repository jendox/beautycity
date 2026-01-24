from django.views.generic import TemplateView

from salons.models import Master, Salon, Service


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        salons = Salon.objects.all().order_by('id')
        context['salons'] = salons
        context['services'] = Service.objects.filter(is_active=True).order_by('id')[:6]
        context['masters'] = Master.objects.filter(is_active=True).select_related('salon').order_by('id')[:6]

        return context
