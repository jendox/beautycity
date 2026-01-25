from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PersonalDataConsent
from appointments.models import Appointment, BookingHold, MasterShift
from appointments.serializers import (
    ApplyPromoSerializer,
    AvailabilityDatesQuerySerializer,
    AvailabilitySlotsQuerySerializer,
    ConfirmAppointmentSerializer,
    CreateHoldSerializer,
    MasterAvailabilityQuerySerializer,
    get_active_promo_by_code,
)
from salons.models import Master, Salon, Service

SLOT_STEP_MINUTES = 30
HOLD_TTL_SECONDS = 5 * 60


def _tz():
    return timezone.get_current_timezone()


def _ensure_session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _day_bounds(day):
    tz = _tz()
    start = timezone.make_aware(datetime.combine(day, time.min), tz)
    end = start + timedelta(days=1)
    return start, end


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and a_end > b_start


def _busy_intervals_for_master(*, master: Master, day_start, day_end, now):
    appts = (
        Appointment.objects.filter(
            master=master,
            status=Appointment.STATUS_BOOKED,
            starts_at__lt=day_end,
            ends_at__gt=day_start,
        )
        .only("starts_at", "ends_at")
        .order_by("starts_at")
    )
    holds = (
        BookingHold.objects.filter(
            master=master,
            expires_at__gt=now,
            starts_at__lt=day_end,
            ends_at__gt=day_start,
        )
        .only("starts_at", "ends_at")
        .order_by("starts_at")
    )
    intervals = [(a.starts_at, a.ends_at) for a in appts] + [(h.starts_at, h.ends_at) for h in holds]
    intervals.sort(key=lambda x: x[0])
    return intervals


def _shifts_for(*, salon: Salon | None, master: Master | None, weekday: int):
    qs = MasterShift.objects.filter(is_active=True, weekday=weekday).select_related("master", "salon")
    if salon:
        qs = qs.filter(salon=salon)
    if master:
        qs = qs.filter(master=master)
    return list(qs.order_by("starts_time", "id"))


def _shift_covers(*, day, shift: MasterShift, starts_at, ends_at) -> bool:
    tz = _tz()
    shift_start = timezone.make_aware(datetime.combine(day, shift.starts_time), tz)
    shift_end = timezone.make_aware(datetime.combine(day, shift.ends_time), tz)
    return starts_at >= shift_start and ends_at <= shift_end


def _iter_slot_starts(*, day, shift: MasterShift, duration_minutes: int):
    tz = _tz()
    start = timezone.make_aware(datetime.combine(day, shift.starts_time), tz)
    end = timezone.make_aware(datetime.combine(day, shift.ends_time), tz)
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)

    current = start
    while current + duration <= end:
        yield current
        current += step


def _available_slots_for_master(*, day, master: Master, salon: Salon, duration_minutes: int, now):
    weekday = day.weekday()
    shifts = [s for s in _shifts_for(salon=salon, master=master, weekday=weekday) if s.salon_id == salon.id]
    if not shifts:
        return []

    day_start, day_end = _day_bounds(day)
    busy = _busy_intervals_for_master(master=master, day_start=day_start, day_end=day_end, now=now)
    duration = timedelta(minutes=duration_minutes)

    slots = []
    for shift in shifts:
        for starts_at in _iter_slot_starts(day=day, shift=shift, duration_minutes=duration_minutes):
            ends_at = starts_at + duration
            if any(_overlaps(starts_at, ends_at, b0, b1) for (b0, b1) in busy):
                continue
            slots.append((starts_at, ends_at))
    return slots


def _available_slots_for_salon(*, day, salon: Salon, duration_minutes: int, now) -> list[tuple[datetime, datetime]]:
    weekday = day.weekday()
    shifts = _shifts_for(salon=salon, master=None, weekday=weekday)
    if not shifts:
        return []

    shifts_by_master: dict[int, list[MasterShift]] = defaultdict(list)
    for s in shifts:
        shifts_by_master[s.master_id].append(s)

    duration = timedelta(minutes=duration_minutes)
    available_by_start: dict[datetime, datetime] = {}

    masters = Master.objects.filter(id__in=list(shifts_by_master.keys()), is_active=True).order_by("id")
    for master in masters:
        day_start, day_end = _day_bounds(day)
        busy = _busy_intervals_for_master(master=master, day_start=day_start, day_end=day_end, now=now)
        for shift in shifts_by_master.get(master.id, []):
            for starts_at in _iter_slot_starts(day=day, shift=shift, duration_minutes=duration_minutes):
                ends_at = starts_at + duration
                if any(_overlaps(starts_at, ends_at, b0, b1) for (b0, b1) in busy):
                    continue
                available_by_start.setdefault(starts_at, ends_at)

    return sorted(available_by_start.items(), key=lambda x: x[0])


def _pricing_for_service(*, service: Service, promo_code_str: str | None, now):
    base_price = int(service.price or 0)
    promo = get_active_promo_by_code(promo_code_str or "", now=now)
    discount_percent = int(promo.discount_percent) if promo else 0
    discount_amount = (base_price * discount_percent) // 100
    total_price = max(0, base_price - discount_amount)
    return {
        "promo": promo,
        "base_price": base_price,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "total_price": total_price,
        "currency": "RUB",
    }


def _resolve_availability_objects(*, service_id: int, salon_id: int | None, master_id: int | None):
    service = Service.objects.filter(pk=service_id, is_active=True).first()
    if not service:
        return Response(data={"detail": "service_not_found"}, status=404)

    salon = None
    if salon_id is not None:
        salon = Salon.objects.filter(pk=salon_id).first()
        if not salon:
            return Response(data={"detail": "salon_not_found"}, status=404)

    master = None
    if master_id is not None:
        master = Master.objects.filter(pk=master_id, is_active=True).first()
        if not master:
            return Response(data={"detail": "master_not_found"}, status=404)

    if not salon and not master:
        return Response(data={"detail": "missing_params"}, status=400)

    return service, salon, master


def _slots_for_master_any_salon(*, day, master: Master, duration_minutes: int, now):
    weekday = day.weekday()
    shifts = _shifts_for(salon=None, master=master, weekday=weekday)
    unique = {}
    for shift in shifts:
        slots = _available_slots_for_master(
            day=day,
            master=master,
            salon=shift.salon,
            duration_minutes=duration_minutes,
            now=now,
        )
        for s0, s1 in slots:
            unique.setdefault(s0, s1)
    return sorted(unique.items(), key=lambda x: x[0])


def _slots_for_request(*, day, service: Service, salon: Salon | None, master: Master | None, now):
    if master and salon:
        return _available_slots_for_master(
            day=day,
            master=master,
            salon=salon,
            duration_minutes=service.duration_minutes,
            now=now,
        )
    if master and not salon:
        return _slots_for_master_any_salon(day=day, master=master, duration_minutes=service.duration_minutes, now=now)
    if salon:
        return _available_slots_for_salon(day=day, salon=salon, duration_minutes=service.duration_minutes, now=now)
    return []


def _slots_to_payload(slots):
    return [
        {"starts_at": s0.isoformat(), "ends_at": s1.isoformat(), "is_available": True}
        for s0, s1 in slots
    ]


def _available_dates_for_request(
    *,
    from_date,
    to_date,
    service: Service,
    salon: Salon | None,
    master: Master | None,
    now,
):
    dates = []
    current = from_date
    while current <= to_date:
        if _slots_for_request(day=current, service=service, salon=salon, master=master, now=now):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _resolve_salon_service_for_hold(*, salon_id: int, service_id: int):
    salon = Salon.objects.filter(pk=salon_id).first()
    if not salon:
        return Response(data={"detail": "salon_not_found"}, status=404)

    service = Service.objects.filter(pk=service_id, is_active=True).first()
    if not service:
        return Response(data={"detail": "service_not_found"}, status=404)

    if service.salon_id != salon.id:
        return Response(data={"detail": "invalid_request"}, status=400)

    return salon, service


def _normalize_starts_at(starts_at):
    if timezone.is_naive(starts_at):
        return timezone.make_aware(starts_at, _tz())
    return starts_at


def _service_duration_minutes(service: Service):
    duration_minutes = int(service.duration_minutes or 0)
    if duration_minutes <= 0:
        return Response(data={"detail": "invalid_request"}, status=400)
    return duration_minutes


def _master_is_available_for_slot(*, master: Master, salon: Salon, starts_at, ends_at, now) -> bool:
    if master.salon_id != salon.id:
        return False

    day = starts_at.astimezone(_tz()).date()
    weekday = day.weekday()
    shifts = _shifts_for(salon=salon, master=master, weekday=weekday)
    if not any(_shift_covers(day=day, shift=s, starts_at=starts_at, ends_at=ends_at) for s in shifts):
        return False

    busy = _busy_intervals_for_master(
        master=master,
        day_start=starts_at - timedelta(hours=24),
        day_end=ends_at + timedelta(hours=24),
        now=now,
    )
    return not any(_overlaps(starts_at, ends_at, b0, b1) for (b0, b1) in busy)


def _select_specific_master_for_hold(*, salon: Salon, starts_at, ends_at, master_id: int, now):
    master = Master.objects.select_for_update().filter(pk=master_id, is_active=True).first()
    if not master:
        return Response(data={"detail": "master_not_found"}, status=404)
    if not _master_is_available_for_slot(master=master, salon=salon, starts_at=starts_at, ends_at=ends_at, now=now):
        return Response(data={"detail": "slot_unavailable"}, status=409)
    return master


def _select_any_master_for_hold(*, salon: Salon, starts_at, ends_at, now):
    weekday = starts_at.astimezone(_tz()).date().weekday()
    shifts = _shifts_for(salon=salon, master=None, weekday=weekday)
    masters_ids = sorted({s.master_id for s in shifts})
    if not masters_ids:
        return Response(data={"detail": "slot_unavailable"}, status=409)

    for candidate_id in masters_ids:
        candidate = Master.objects.select_for_update().filter(pk=candidate_id, is_active=True).first()
        if not candidate:
            continue
        if _master_is_available_for_slot(master=candidate, salon=salon, starts_at=starts_at, ends_at=ends_at, now=now):
            return candidate

    return Response(data={"detail": "slot_unavailable"}, status=409)


def _select_master_for_hold(*, salon: Salon, starts_at, ends_at, master_id: int | None, now):
    if master_id is not None:
        return _select_specific_master_for_hold(
            salon=salon,
            starts_at=starts_at,
            ends_at=ends_at,
            master_id=master_id,
            now=now,
        )
    return _select_any_master_for_hold(salon=salon, starts_at=starts_at, ends_at=ends_at, now=now)


class AvailabilityDatesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = AvailabilityDatesQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        resolved = _resolve_availability_objects(
            service_id=data["service_id"],
            salon_id=data.get("salon_id"),
            master_id=data.get("master_id"),
        )
        if isinstance(resolved, Response):
            return resolved
        service, salon, master = resolved

        now = timezone.now()
        dates = _available_dates_for_request(
            from_date=data["from_"],
            to_date=data["to"],
            service=service,
            salon=salon,
            master=master,
            now=now,
        )

        return Response(
            data={
                "from": data["from_"].isoformat(),
                "to": data["to"].isoformat(),
                "timezone": str(_tz()),
                "dates": dates,
            },
        )


class AvailabilitySlotsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = AvailabilitySlotsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        resolved = _resolve_availability_objects(
            service_id=data["service_id"],
            salon_id=data.get("salon_id"),
            master_id=data.get("master_id"),
        )
        if isinstance(resolved, Response):
            return resolved
        service, salon, master = resolved

        now = timezone.now()
        day = data["date"]
        slots = _slots_for_request(day=day, service=service, salon=salon, master=master, now=now)

        return Response(
            data={
                "date": day.isoformat(),
                "timezone": str(_tz()),
                "slot_minutes_step": SLOT_STEP_MINUTES,
                "slots": _slots_to_payload(slots),
            },
        )


class MasterAvailabilityAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, master_id: int):
        master = Master.objects.filter(pk=master_id, is_active=True).first()
        if not master:
            return Response(data={"detail": "master_not_found"}, status=404)
        serializer = MasterAvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = Service.objects.filter(pk=data["service_id"], is_active=True).first()
        if not service:
            return Response(data={"detail": "service_not_found"}, status=404)
        day = data["date"]
        now = timezone.now()

        weekday = day.weekday()
        shifts = _shifts_for(salon=None, master=master, weekday=weekday)
        results = []
        seen_salon_ids = set()
        for shift in shifts:
            if shift.salon_id in seen_salon_ids:
                continue
            seen_salon_ids.add(shift.salon_id)
            slots = _available_slots_for_master(
                day=day,
                master=master,
                salon=shift.salon,
                duration_minutes=service.duration_minutes,
                now=now,
            )
            results.append(
                {
                    "salon": {"id": shift.salon_id, "name": shift.salon.name, "address": shift.salon.address},
                    "slots": _slots_to_payload(slots),
                },
            )

        return Response(
            data={
                "date": day.isoformat(),
                "timezone": str(_tz()),
                "results": results,
            },
        )


class BookingHoldListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateHoldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        resolved = _resolve_salon_service_for_hold(salon_id=data["salon_id"], service_id=data["service_id"])
        if isinstance(resolved, Response):
            return resolved
        salon, service = resolved

        now = timezone.now()
        starts_at = _normalize_starts_at(data["starts_at"])

        duration = _service_duration_minutes(service)
        if isinstance(duration, Response):
            return duration
        ends_at = starts_at + timedelta(minutes=duration)

        promo_code_str = (data.get("promo_code") or "").strip()
        pricing = _pricing_for_service(service=service, promo_code_str=promo_code_str, now=now)
        session_key = _ensure_session_key(request)

        with transaction.atomic():
            master = _select_master_for_hold(
                salon=salon,
                starts_at=starts_at,
                ends_at=ends_at,
                master_id=data.get("master_id"),
                now=now,
            )
            if isinstance(master, Response):
                return master

            hold = BookingHold.objects.create(
                session_key=session_key,
                salon=salon,
                service=service,
                master=master,
                starts_at=starts_at,
                ends_at=ends_at,
                expires_at=now + timedelta(seconds=HOLD_TTL_SECONDS),
                promo_code=pricing["promo"],
                base_price=pricing["base_price"],
                discount_percent=pricing["discount_percent"],
                discount_amount=pricing["discount_amount"],
                total_price=pricing["total_price"],
                currency=pricing["currency"],
            )

        return Response(
            status=201,
            data={
                "hold_id": hold.public_id,
                "expires_at": hold.expires_at.isoformat(),
                "summary": _hold_summary(hold),
            },
        )


class BookingHoldDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, hold_id: str):
        hold_id = (hold_id or "").strip()
        if hold_id.startswith("hld_"):
            hold_id = hold_id[4:]
        hold = (
            BookingHold.objects.filter(pk=hold_id)
            .select_related("salon", "service", "master", "promo_code")
            .first()
        )
        if not hold:
            return Response(data={"detail": "hold_not_found"}, status=404)

        if hold.session_key != request.session.session_key:
            return Response(data={"detail": "forbidden"}, status=403)

        if hold.is_expired():
            return Response(data={"detail": "hold_expired"}, status=410)

        return Response(
            data={
                "hold_id": hold.public_id,
                "expires_at": hold.expires_at.isoformat(),
                "summary": _hold_summary(hold),
            },
        )

    def delete(self, request, hold_id: str):
        hold_id = (hold_id or "").strip()
        if hold_id.startswith("hld_"):
            hold_id = hold_id[4:]
        hold = BookingHold.objects.filter(pk=hold_id).first()
        if not hold:
            return Response(data={"detail": "hold_not_found"}, status=404)
        if hold.session_key != request.session.session_key:
            return Response(data={"detail": "forbidden"}, status=403)
        hold.delete()
        return Response(status=204)


class BookingHoldApplyPromoAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, hold_id: str):
        hold_id_raw = (hold_id or "").strip()
        if hold_id_raw.startswith("hld_"):
            hold_id_raw = hold_id_raw[4:]
        hold = (
            BookingHold.objects.select_related("service", "salon", "master", "promo_code")
            .filter(pk=hold_id_raw)
            .first()
        )
        if not hold:
            return Response(data={"detail": "hold_not_found"}, status=404)
        if hold.session_key != request.session.session_key:
            return Response(data={"detail": "forbidden"}, status=403)
        if hold.is_expired():
            return Response(data={"detail": "hold_expired"}, status=410)

        serializer = ApplyPromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["promo_code"]

        now = timezone.now()
        pricing = _pricing_for_service(service=hold.service, promo_code_str=code, now=now)
        if not pricing["promo"]:
            return Response(data={"detail": "invalid_promo_code"}, status=400)

        hold.promo_code = pricing["promo"]
        hold.base_price = pricing["base_price"]
        hold.discount_percent = pricing["discount_percent"]
        hold.discount_amount = pricing["discount_amount"]
        hold.total_price = pricing["total_price"]
        hold.currency = pricing["currency"]
        hold.save(
            update_fields=[
                "promo_code",
                "base_price",
                "discount_percent",
                "discount_amount",
                "total_price",
                "currency",
            ],
        )

        return Response(
            data={
                "hold_id": hold.public_id,
                "expires_at": hold.expires_at.isoformat(),
                "summary": _hold_summary(hold),
            },
        )


def _get_hold_for_confirmation(*, hold_id: str, session_key: str | None, now):
    hold = (
        # NOTE: `master`/`promo_code` are nullable FKs. With Postgres, `SELECT ... FOR UPDATE`
        # cannot lock rows on the nullable side of an outer join, so we avoid `select_related`
        # for nullable relations here.
        BookingHold.objects.select_for_update()
        .select_related("salon", "service")
        .filter(pk=hold_id)
        .first()
    )
    if not hold:
        return Response(data={"detail": "hold_not_found"}, status=404)
    if hold.session_key != session_key:
        return Response(data={"detail": "forbidden"}, status=403)
    if hold.is_expired(now=now):
        return Response(data={"detail": "hold_expired"}, status=410)
    return hold


def _master_has_conflict(*, master: Master, hold: BookingHold, now) -> bool:
    if Appointment.objects.filter(
        master=master,
        status=Appointment.STATUS_BOOKED,
        starts_at__lt=hold.ends_at,
        ends_at__gt=hold.starts_at,
    ).exists():
        return True
    return BookingHold.objects.filter(
        master=master,
        expires_at__gt=now,
        starts_at__lt=hold.ends_at,
        ends_at__gt=hold.starts_at,
    ).exclude(pk=hold.pk).exists()


def _confirm_hold_to_appointment(*, request, hold_id: str, client: dict, now, user=None):
    phone_e164 = client.get("phone_e164", "")
    name = (client.get("name") or "").strip()
    comment = (client.get("comment") or "").strip()
    with transaction.atomic():
        hold = _get_hold_for_confirmation(hold_id=hold_id, session_key=request.session.session_key, now=now)
        if isinstance(hold, Response):
            return hold

        master = None
        if hold.master_id:
            master = Master.objects.select_for_update().get(pk=hold.master_id)
            if _master_has_conflict(master=master, hold=hold, now=now):
                return Response(data={"detail": "slot_unavailable"}, status=409)

        appointment = Appointment.objects.create(
            user=user,
            client_phone=phone_e164,
            client_name=name,
            comment=comment,
            salon=hold.salon,
            service=hold.service,
            master=hold.master,
            starts_at=hold.starts_at,
            ends_at=hold.ends_at,
            promo_code=hold.promo_code,
            base_price=hold.base_price,
            discount_percent=hold.discount_percent,
            discount_amount=hold.discount_amount,
            total_price=hold.total_price,
            currency=hold.currency,
            status=Appointment.STATUS_BOOKED,
            is_paid=False,
        )

        hold.delete()
        return appointment


class AppointmentCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data.get("pd_consent"):
            return Response(data={"detail": "pd_consent_required"}, status=400)

        now = timezone.now()

        phone_e164 = data["phone"]
        PersonalDataConsent.objects.get_or_create(phone=phone_e164)
        user = None
        if getattr(request, "user", None) and request.user.is_authenticated and not request.user.is_staff:
            user = request.user
        appointment = _confirm_hold_to_appointment(
            request=request,
            hold_id=data["hold_id"],
            client={
                "phone_e164": phone_e164,
                "name": data.get("name") or "",
                "comment": data.get("comment") or "",
            },
            now=now,
            user=user,
        )
        if isinstance(appointment, Response):
            return appointment

        return Response(
            status=201,
            data={
                "appointment_id": appointment.id,  # type: ignore[union-attr]
                "summary": {
                    **_hold_summary(appointment),  # type: ignore[arg-type]
                    "status": appointment.status,  # type: ignore[union-attr]
                    "is_paid": appointment.is_paid,  # type: ignore[union-attr]
                },
            },
        )


def _hold_summary(obj):
    # Shared summary builder for hold and appointment.
    salon = obj.salon
    service = obj.service
    master = getattr(obj, "master", None)
    return {
        "salon": {"id": salon.id, "name": salon.name, "address": salon.address},
        "service": {
            "id": service.id,
            "title": service.title,
            "price": obj.base_price,
            "currency": obj.currency,
            "duration_minutes": service.duration_minutes,
        },
        "master": {
            "id": master.id,
            "name": master.name,
            "image_url": master.image.url if getattr(master, "image", None) else None,
        }
        if master
        else None,
        "starts_at": obj.starts_at.isoformat(),
        "ends_at": obj.ends_at.isoformat(),
        "total_price": obj.total_price,
        "currency": obj.currency,
        "promo_code": obj.promo_code.code if getattr(obj, "promo_code", None) else None,
        "discount_percent": obj.discount_percent,
        "discount_amount": obj.discount_amount,
    }


class MyAppointmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Appointment.objects.filter(user=request.user)
            .select_related("salon", "service", "master")
            .order_by("-starts_at")
        )
        results = []
        for appt in qs:
            results.append(
                {
                    "appointment_id": appt.id,
                    "salon": {"id": appt.salon_id, "name": appt.salon.name, "address": appt.salon.address},
                    "service": {"id": appt.service_id, "title": appt.service.title},
                    "master": {"id": appt.master_id, "name": appt.master.name} if appt.master else None,
                    "starts_at": appt.starts_at.isoformat(),
                    "ends_at": appt.ends_at.isoformat(),
                    "status": appt.status,
                    "is_paid": appt.is_paid,
                    "total_price": appt.total_price,
                    "currency": appt.currency,
                },
            )
        return Response(data={"results": results})
