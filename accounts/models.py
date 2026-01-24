from datetime import timedelta
from typing import Self

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    username = models.CharField(max_length=100, unique=False, blank=True, null=False)
    phone = PhoneNumberField(unique=True)
    pd_consent_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username or str(self.phone)

    @property
    def display_name(self):
        full_name = f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()
        if full_name:
            return full_name
        if self.username:
            return self.username
        return str(self.phone)


class PersonalDataConsent(models.Model):
    phone = models.CharField(max_length=32, unique=True, db_index=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Согласие на обработку ПД"
        verbose_name_plural = "Согласия на обработку ПД"

    def __str__(self):
        return self.phone


class PhoneOTP(models.Model):
    phone = models.CharField(max_length=32, db_index=True)
    code_hash = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)

    attempts = models.PositiveSmallIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_used(self):
        return self.used_at is not None

    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code_hash)

    @classmethod
    def create_otp(cls, phone: str, raw_code: str, ttl_seconds: int = 300) -> Self:
        return cls.objects.create(
            phone=phone,
            code_hash=make_password(raw_code),
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        )
