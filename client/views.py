from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.generic import TemplateView

from appointments.models import Appointment


class CabinetView(LoginRequiredMixin, TemplateView):
    template_name = 'notes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        qs = (
            Appointment.objects.filter(user=self.request.user, status=Appointment.STATUS_BOOKED)
            .select_related("salon", "service", "master")
            .order_by("starts_at")
        )

        upcoming = list(qs.filter(starts_at__gte=now).order_by("starts_at")[:5])
        history = list(qs.filter(starts_at__lt=now).order_by("-starts_at")[:5])

        for appt in upcoming:
            appt.is_upcoming = True  # type: ignore[attr-defined]
        for appt in history:
            appt.is_upcoming = False  # type: ignore[attr-defined]

        unpaid_total = qs.filter(starts_at__gte=now, is_paid=False).aggregate(
            total=Coalesce(Sum("total_price"), 0),
        )["total"]

        context.update(
            {
                "appointments_upcoming": upcoming,
                "appointments_history": history,
                "unpaid_total": int(unpaid_total or 0),
            },
        )
        return context
