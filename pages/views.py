from django.views.generic import TemplateView

from salons.models import Salon


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        salons = Salon.objects.all().order_by('id')
        context['salons'] = salons

        return context
