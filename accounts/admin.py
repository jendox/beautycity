from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    search_fields = ("phone", "username", "first_name", "last_name")
    list_display = ("id", "phone", "username", "first_name", "last_name", "is_staff", "is_superuser")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Персональные данные", {"fields": ("first_name", "last_name", "email")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone", "username", "first_name", "last_name", "password1", "password2", "is_staff", "is_superuser",
            ),
        }),
    )
