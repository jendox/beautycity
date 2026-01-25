from __future__ import annotations

import uuid
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from salons.models import Master, Salon, Service

DISCOUNT_PERCENT_MAX = 100


class PromoCode(models.Model):
    code = models.CharField("Код", max_length=32)
    discount_percent = models.PositiveSmallIntegerField("Скидка, %")
    is_active = models.BooleanField("Активен", default=True)
    valid_from = models.DateTimeField("Действует с", blank=True, null=True)
    valid_to = models.DateTimeField("Действует до", blank=True, null=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_percent__gte=0) & models.Q(discount_percent__lte=DISCOUNT_PERCENT_MAX),
                name="appointments_promocode_discount_percent_range",
            ),
            models.UniqueConstraint(Lower("code"), name="appointments_promocode_code_ci_unique"),
        ]

    def __str__(self) -> str:
        return self.code

    def clean(self):
        if self.code:
            self.code = self.code.strip()
        if not self.code:
            raise ValidationError({"code": "required"})
        if self.discount_percent > DISCOUNT_PERCENT_MAX:
            raise ValidationError({"discount_percent": "invalid"})

    def is_valid_at(self, now: datetime | None = None) -> bool:
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True


class MasterShift(models.Model):
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name="Мастер",
    )
    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="master_shifts",
        verbose_name="Салон",
    )
    weekday = models.PositiveSmallIntegerField("День недели", help_text="0=Пн ... 6=Вс")
    starts_time = models.TimeField("Начало")
    ends_time = models.TimeField("Окончание")
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Смена мастера"
        verbose_name_plural = "Смены мастеров"
        indexes = [
            models.Index(fields=["salon", "weekday"], name="app_shift_sal_wd_idx"),
            models.Index(fields=["master", "weekday"], name="app_shift_mst_wd_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(weekday__gte=0) & models.Q(weekday__lte=6), name="shift_weekday"),
        ]

    def __str__(self) -> str:
        return f"{self.master} @ {self.salon} ({self.weekday})"

    def clean(self):
        if self.ends_time <= self.starts_time:
            raise ValidationError({"ends_time": "ends_before_starts"})


class BookingHold(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, db_index=True)

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name="booking_holds")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="booking_holds")
    master = models.ForeignKey(Master, on_delete=models.SET_NULL, blank=True, null=True, related_name="booking_holds")

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)

    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, blank=True, null=True)
    base_price = models.PositiveIntegerField(default=0)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    total_price = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="RUB")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["master", "starts_at"], name="hold_master_starts_idx"),
            models.Index(fields=["expires_at"], name="hold_expires_at_idx"),
        ]

    def __str__(self) -> str:
        return f"hld_{self.id.hex}"

    @property
    def public_id(self) -> str:
        return f"hld_{self.id.hex}"

    def is_expired(self, now: timezone.datetime | None = None) -> bool:
        now = now or timezone.now()
        return self.expires_at <= now


class Appointment(models.Model):
    STATUS_BOOKED = "booked"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_BOOKED, "Записан"),
        (STATUS_CANCELLED, "Отменён"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointments",
        verbose_name="Клиент",
    )
    client_phone = PhoneNumberField("Телефон клиента", region="RU", db_index=True)
    client_name = models.CharField("Имя клиента", max_length=255, blank=True)
    comment = models.TextField("Комментарий", blank=True)

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name="appointments", verbose_name="Салон")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments", verbose_name="Услуга")
    master = models.ForeignKey(
        Master, on_delete=models.SET_NULL, blank=True, null=True, related_name="appointments", verbose_name="Мастер",
    )

    starts_at = models.DateTimeField("Начало", db_index=True)
    ends_at = models.DateTimeField("Окончание")

    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Промокод")
    base_price = models.PositiveIntegerField("Цена", default=0)
    discount_percent = models.PositiveSmallIntegerField("Скидка", default=0)
    discount_amount = models.PositiveIntegerField("Сумма скидки", default=0)
    total_price = models.PositiveIntegerField("К опалте", default=0)
    currency = models.CharField("Валюта", max_length=3, default="RUB")

    status = models.CharField("Статус", max_length=16, choices=STATUS_CHOICES, default=STATUS_BOOKED)
    is_paid = models.BooleanField("Оплачено", default=False)

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        indexes = [
            models.Index(fields=["master", "starts_at"], name="appt_master_starts_idx"),
            models.Index(fields=["salon", "starts_at"], name="appt_salon_starts_idx"),
        ]

    def __str__(self) -> str:
        return f"#{self.id} {self.client_phone} {self.starts_at}"
