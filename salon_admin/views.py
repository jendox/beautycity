from datetime import datetime, time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.generic import TemplateView

from appointments.models import Appointment
from salons.models import SalonAdmin


class SalonAdminView(LoginRequiredMixin, TemplateView):
    template_name = 'admin.html'

    MONTHS_IN_YEAR = 12

    @classmethod
    def _month_range(cls, today):
        start = today.replace(day=1)
        if start.month == cls.MONTHS_IN_YEAR:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    @staticmethod
    def _year_range(today):
        start = today.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
        return start, end

    @staticmethod
    def _start_dt(day, tz):
        return timezone.make_aware(datetime.combine(day, time.min), tz)

    def _stats_for_salon(self, salon):
        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        month_start, month_end = self._month_range(today)
        year_start, year_end = self._year_range(today)
        month_range = (self._start_dt(month_start, tz), self._start_dt(month_end, tz))
        year_range = (self._start_dt(year_start, tz), self._start_dt(year_end, tz))

        qs = Appointment.objects.filter(salon=salon, status=Appointment.STATUS_BOOKED).only(
            "starts_at",
            "is_paid",
            "total_price",
        )
        month_qs = qs.filter(starts_at__gte=month_range[0], starts_at__lt=month_range[1])
        year_qs = qs.filter(starts_at__gte=year_range[0], starts_at__lt=year_range[1])

        visits_month = month_qs.count()
        visits_year = year_qs.count()
        paid_sum_month = month_qs.filter(is_paid=True).aggregate(total=Coalesce(Sum("total_price"), 0))["total"]

        return {
            "paid_sum_month": int(paid_sum_month or 0),
            "visits_month": int(visits_month),
            "visits_year": int(visits_year),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        salon_admin = (
            SalonAdmin.objects.filter(user=self.request.user, is_active=True)
            .select_related("salon")
            .first()
        )
        if not salon_admin:
            raise PermissionDenied

        context.update(
            {
                "salon": salon_admin.salon,
                **self._stats_for_salon(salon_admin.salon),
            },
        )
        return context
