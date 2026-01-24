from django.core.exceptions import ValidationError
from django.db import models

from config import settings


class Salon(models.Model):
    name = models.CharField('Название', max_length=100)
    address = models.CharField('Адрес', max_length=255, blank=True)
    image = models.FileField('Изображение', upload_to='salons/', blank=True, null=True)

    class Meta:
        verbose_name = 'Салон'
        verbose_name_plural = 'Салоны'

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name='service_categories',
        verbose_name='Салон',
    )
    title = models.CharField('Название', max_length=100)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'

        unique_together = ('salon', 'title')
        ordering = ('sort_order', 'id')

    def __str__(self):
        return self.title


class Service(models.Model):
    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Салон',
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='services',
        verbose_name='Категория услуги',
    )
    title = models.CharField('Название', max_length=255)
    image = models.FileField('Изображение', upload_to='services/', blank=True, null=True)
    duration_minutes = models.PositiveIntegerField('Продолжительность', default=60)
    price = models.PositiveIntegerField('Цена', default=0)
    is_active = models.BooleanField('Активна', default=True)

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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salon_adminships',
        verbose_name='Пользователь',
    )
    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name='salon_admins',
        verbose_name='Салон',
    )
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Администратор салона'
        verbose_name_plural = 'Администраторы салонов'
        unique_together = ('user', 'salon')

    def __str__(self):
        return f"{self.user} -> {self.salon}"


class Master(models.Model):
    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name='masters',
        verbose_name='Салон',
    )
    name = models.CharField('Имя', max_length=255)
    image = models.FileField('Изображение', upload_to='masters/', blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'

    def __str__(self):
        return self.name
