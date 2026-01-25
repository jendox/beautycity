from datetime import timedelta

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from accounts.models import PersonalDataConsent
from accounts.phone import normalize_phone, phone_to_user_field
from appointments.models import Appointment, BookingHold, MasterShift, PromoCode
from salons.models import Master, Salon, Service

from . import api_views


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active",)
    search_fields = ("code",)


@admin.register(MasterShift)
class MasterShiftAdmin(admin.ModelAdmin):
    list_display = ("master", "salon", "weekday", "starts_time", "ends_time", "is_active")
    list_filter = ("salon", "weekday", "is_active")


@admin.register(BookingHold)
class BookingHoldAdmin(admin.ModelAdmin):
    list_display = ("public_id", "salon", "service", "master", "starts_at", "expires_at")
    list_filter = ("salon",)
    search_fields = ("session_key",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "client_phone", "salon", "service", "master", "starts_at", "status", "is_paid", "total_price")
    list_filter = ("salon", "status", "is_paid")
    search_fields = ("client_phone", "client_name")
    change_list_template = "admin/appointments/appointment/change_list.html"

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Prevent creating Appointment via the raw ModelAdmin form.
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "operator-booking/",
                self.admin_site.admin_view(self.operator_booking_view),
                name="appointments_appointment_operator_booking",
            ),
        ]
        return custom + urls

    class OperatorBookingForm(forms.Form):
        salon = forms.ModelChoiceField(queryset=Salon.objects.all(), label="Салон")
        service = forms.ModelChoiceField(queryset=Service.objects.filter(is_active=True), label="Услуга")
        master = forms.ModelChoiceField(
            queryset=Master.objects.filter(is_active=True),
            required=False,
            empty_label="Любой мастер",
            label="Мастер",
        )
        starts_at = forms.SplitDateTimeField(
            label="Начало",
            help_text="Дата и время начала услуги",
            widget=AdminSplitDateTime(),
        )
        phone = forms.CharField(label="Телефон клиента", help_text="Например: +7 999 111-22-33")
        name = forms.CharField(label="Имя клиента", required=False)
        comment = forms.CharField(label="Комментарий", required=False, widget=forms.Textarea(attrs={"rows": 3}))
        promo_code = forms.CharField(label="Промокод", required=False)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            salon_id = self._selected_salon_id()
            if salon_id:
                self.fields["service"].queryset = Service.objects.filter(salon_id=salon_id, is_active=True)
                self.fields["master"].queryset = Master.objects.filter(salon_id=salon_id, is_active=True)
            else:
                self.fields["service"].queryset = Service.objects.none()
                self.fields["master"].queryset = Master.objects.none()

        @staticmethod
        def _to_int(value) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        def _selected_salon_id(self) -> int | None:
            salon_id = None
            if self.is_bound:
                salon_id = self._to_int((self.data.get("salon") or "").strip() or None)
            else:
                initial = self.initial.get("salon")
                if isinstance(initial, Salon):
                    salon_id = initial.id
                else:
                    salon_id = self._to_int(initial)

            if not salon_id:
                first = Salon.objects.order_by("id").first()
                if first:
                    self.initial["salon"] = first
                    salon_id = first.id

            return salon_id

        def clean_phone(self):
            raw = self.cleaned_data.get("phone") or ""
            try:
                return normalize_phone(raw)
            except ValueError:
                raise forms.ValidationError("Неверный телефон.") from None

        def clean(self):
            cleaned = super().clean()
            salon = cleaned.get("salon")
            service = cleaned.get("service")
            master = cleaned.get("master")
            if salon and service and service.salon_id != salon.id:
                self.add_error("service", "Услуга должна принадлежать выбранному салону.")
            if salon and master and master.salon_id != salon.id:
                self.add_error("master", "Мастер должен принадлежать выбранному салону.")
            return cleaned

    def operator_booking_view(self, request: HttpRequest):
        if not request.user.has_perm("appointments.add_appointment"):
            raise PermissionDenied

        if request.method == "POST":
            form_data = request.POST
        else:
            form_data = request.GET if request.GET else None
        form = self.OperatorBookingForm(form_data)
        if request.method == "POST" and form.is_valid():
            try:
                appointment = self._create_operator_appointment(request=request, cleaned=form.cleaned_data)
                self.message_user(request, f"Запись создана (ID {appointment.id}).", level=messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:appointments_appointment_change", args=[appointment.id]))
            except forms.ValidationError as exc:
                form.add_error(None, str(exc))
            except Exception:
                form.add_error(None, "Не удалось создать запись. Попробуйте другое время.")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Создать запись (оператор)",
            "form": form,
        }
        return TemplateResponse(request, "admin/appointments/appointment/operator_booking.html", context)

    def _create_operator_appointment(self, *, request: HttpRequest, cleaned: dict) -> Appointment:
        now = timezone.now()
        salon: Salon = cleaned["salon"]
        service: Service = cleaned["service"]
        master: Master | None = cleaned.get("master")
        starts_at = api_views._normalize_starts_at(cleaned["starts_at"])
        phone_e164: str = cleaned["phone"]
        name = (cleaned.get("name") or "").strip()
        comment = (cleaned.get("comment") or "").strip()
        promo_code_str = (cleaned.get("promo_code") or "").strip()

        salon, service = self._validate_salon_service(salon=salon, service=service)
        hold = self._create_hold_for_operator(
            request=request,
            payload={
                "salon": salon,
                "service": service,
                "master": master,
                "starts_at": starts_at,
                "promo_code_str": promo_code_str,
            },
            now=now,
        )
        PersonalDataConsent.objects.get_or_create(phone=phone_e164)
        user_to_link = self._resolve_user_for_phone(phone_e164)

        appointment = api_views._confirm_hold_to_appointment(
            request=request,
            hold_id=hold.id.hex,
            client={"phone_e164": phone_e164, "name": name, "comment": comment},
            now=now,
            user=user_to_link,
        )
        if isinstance(appointment, api_views.Response):
            detail = (appointment.data or {}).get("detail")  # type: ignore[union-attr]
            raise forms.ValidationError(detail or "slot_unavailable")
        return appointment

    def _validate_salon_service(self, *, salon: Salon, service: Service) -> tuple[Salon, Service]:
        resolved = api_views._resolve_salon_service_for_hold(salon_id=salon.id, service_id=service.id)
        if isinstance(resolved, api_views.Response):
            detail = (resolved.data or {}).get("detail")  # type: ignore[union-attr]
            raise forms.ValidationError(detail or "invalid_request")
        return resolved

    def _create_hold_for_operator(self, *, request: HttpRequest, payload: dict, now) -> BookingHold:
        salon: Salon = payload["salon"]
        service: Service = payload["service"]
        master: Master | None = payload.get("master")
        starts_at = payload["starts_at"]
        promo_code_str = payload.get("promo_code_str") or ""
        duration = api_views._service_duration_minutes(service)
        if isinstance(duration, api_views.Response):
            raise forms.ValidationError("invalid_request")
        ends_at = starts_at + timedelta(minutes=duration)

        pricing = api_views._pricing_for_service(service=service, promo_code_str=promo_code_str, now=now)
        session_key = api_views._ensure_session_key(request)

        with api_views.transaction.atomic():
            selected_master = api_views._select_master_for_hold(
                salon=salon,
                starts_at=starts_at,
                ends_at=ends_at,
                master_id=master.id if master else None,
                now=now,
            )
            if isinstance(selected_master, api_views.Response):
                detail = (selected_master.data or {}).get("detail")  # type: ignore[union-attr]
                raise forms.ValidationError(detail or "slot_unavailable")

            return BookingHold.objects.create(
                session_key=session_key,
                salon=salon,
                service=service,
                master=selected_master,
                starts_at=starts_at,
                ends_at=ends_at,
                expires_at=now + timedelta(seconds=api_views.HOLD_TTL_SECONDS),
                promo_code=pricing["promo"],
                base_price=pricing["base_price"],
                discount_percent=pricing["discount_percent"],
                discount_amount=pricing["discount_amount"],
                total_price=pricing["total_price"],
                currency=pricing["currency"],
            )

    def _resolve_user_for_phone(self, phone_e164: str):
        User = get_user_model()
        user = User.objects.filter(phone=phone_to_user_field(phone_e164)).first()
        if user and (user.is_staff or user.is_superuser):
            return None
        return user
