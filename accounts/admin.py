from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/accounts/customuser/change_list.html"

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

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["clients_count"] = (
            CustomUser.objects.filter(is_staff=False, is_superuser=False)
            .exclude(salon_adminships__isnull=False)
            .distinct()
            .count()
        )
        return super().changelist_view(request, extra_context=extra_context)
