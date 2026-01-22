from django.core.exceptions import ValidationError
from django.db import models

from config import settings


class Salon(models.Model):
    name = models.CharField('Название', max_length=100)
    address = models.CharField('Адрес', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Салон'
        verbose_name_plural = 'Салоны'

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='service_categories')
    title = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'

        unique_together = ('salon', 'title')
        ordering = ('sort_order', 'id')

    def __str__(self):
        return self.title


class Service(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='services',
    )
    title = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(default=60)
    price = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ('id',)

    def __str__(self):
        return self.title

    def clean(self):
        if self.category and self.category.salon_id != self.salon.id:
            raise ValidationError('Категория должна принадлежать тому же салону, что и услуга')


class SalonAdmin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='salon_adminships')
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='salon_admins')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Администратор салона'
        verbose_name_plural = 'Администраторы салонов'
        unique_together = ('user', 'salon')

    def __str__(self):
        return f"{self.user} -> {self.salon}"


class Master(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='masters')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'

    def __str__(self):
        return self.name
