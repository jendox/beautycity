from django.contrib import admin

from .models import Master, Salon, SalonAdmin as SalonAdminModel, Service, ServiceCategory


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address")
    search_fields = ("name", "address")
    ordering = ("id",)


@admin.register(SalonAdminModel)
class SalonAdminAdmin(admin.ModelAdmin):
    list_display = ("id", "salon", "user", "is_active")
    list_filter = ("is_active", "salon")
    search_fields = ("salon__name", "user__phone", "user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user", "salon")
    ordering = ("salon", "user")


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "salon", "sort_order", "is_active")
    list_filter = ("salon", "is_active")
    search_fields = ("title", "salon__name")
    ordering = ("salon", "sort_order", "id")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "salon", "category", "price", "duration_minutes", "is_active")
    list_filter = ("salon", "category", "is_active")
    search_fields = ("title", "salon__name", "category__title")
    ordering = ("salon", "id")
    list_editable = ("price", "duration_minutes", "is_active")
    autocomplete_fields = ("salon", "category")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем список категорий по выбранному салону.
        Работает так:
        - если сервис редактируется: берём salon из объекта
        - если сервис создаётся с ?salon=<id> в url: берём его
        Иначе показываем все категории (на MVP ок).
        """
        if db_field.name == "category":
            salon_id = None

            # 1) при редактировании можно достать object_id из url
            # /admin/app/service/<object_id>/change/
            try:
                object_id = request.resolver_match.kwargs.get("object_id")
            except Exception:
                object_id = None

            if object_id:
                try:
                    obj = Service.objects.only("salon_id").get(pk=object_id)
                    salon_id = obj.salon_id
                except Service.DoesNotExist:
                    salon_id = None

            # 2) при создании можно передать ?salon=ID
            if salon_id is None:
                salon_id = request.GET.get("salon")

            if salon_id:
                kwargs["queryset"] = ServiceCategory.objects.filter(salon_id=salon_id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "salon", "is_active")
    list_filter = ("salon", "is_active")
    search_fields = ("name", "salon__name")
    ordering = ("salon", "name")
    autocomplete_fields = ("salon",)
