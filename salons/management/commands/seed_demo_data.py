# salons/management/commands/seed_demo_data.py
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from salons.models import Master, Salon, SalonAdmin, Service, ServiceCategory

User = get_user_model()


def _money_to_int(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0


class Command(BaseCommand):
    help = "Seed demo data (salons, admins, categories, services, masters) from frontend templates"

    @transaction.atomic
    def handle(self, *args, **options):
        salons_payload = [
            {"name": "BeautyCity Пушкинская", "address": "ул. Пушкинская, д. 78А"},
            {"name": "BeautyCity Ленина", "address": "ул. Ленина, д. 211"},
            {"name": "BeautyCity Красная", "address": "ул. Красная, д. 10"},
        ]

        categories_services = [
            ("Парикмахерские услуги", [
                ("Окрашивание волос", "5 000 ₽"),
                ("Укладка волос", "1 500 ₽"),
            ]),
            ("Ногтевой сервис", [
                ("Маникюр. Классический", "1 400 ₽"),
                ("Педикюр", "1 400 ₽"),
                ("Наращивание ногтей", "1 400 ₽"),
            ]),
            ("Макияж", [
                ("Дневной макияж", "1 400 ₽"),
                ("Свадебный макияж", "3 000 ₽"),
                ("Вечерний макияж", "2 000 ₽"),
            ]),
        ]

        masters_by_salon = {
            "BeautyCity Пушкинская": [
                "Елизавета Лапина",
                "Анна Сергеева",
                "Ева Колесова",
                "Мария Суворова",
                "Мария Максимова",
                "Анастасия Сергеева",
            ],
            "BeautyCity Ленина": [
                "Дарья Мартынова",
                "Амина Абрамова",
                "Милана Романова",
                "Диана Чернова",
                "Полина Лукьянова",
                "Вера Дмитриева",
            ],
            "BeautyCity Красная": [
                "Зоя Матвеева",
                "Мария Родина",
                "Дарья Попова",
                "Ева Семенова",
            ],
        }

        salon_admins_payload = {
            "BeautyCity Пушкинская": {"name": "Анна Волкова", "phone": "+79990000001"},
            "BeautyCity Ленина": {"name": "Ирина Смирнова", "phone": "+79990000002"},
            "BeautyCity Красная": {"name": "Ольга Кузнецова", "phone": "+79990000003"},
        }

        created = {
            "salons": 0,
            "admin_users": 0,
            "admin_links": 0,
            "categories": 0,
            "services": 0,
            "masters": 0,
        }

        # 1) Create / update salons
        salons: dict[str, Salon] = {}
        for s in salons_payload:
            obj, was_created = Salon.objects.get_or_create(
                name=s["name"],
                defaults={"address": s["address"]},
            )
            if obj.address != s["address"]:
                obj.address = s["address"]
                obj.save(update_fields=["address"])

            salons[obj.name] = obj
            created["salons"] += int(was_created)

        # 1.1) Create / link salon admins
        for salon_name, admin_data in salon_admins_payload.items():
            salon = salons.get(salon_name)
            if not salon:
                continue

            full_name = admin_data["name"].strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""
            phone = admin_data["phone"].strip()

            user, user_created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "username": f"admin_{salon.id}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                },
            )
            if user_created:
                try:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                except Exception:
                    pass

            link, link_created = SalonAdmin.objects.get_or_create(
                salon=salon,
                user=user,
                defaults={"is_active": True},
            )

            created["admin_users"] += int(user_created)
            created["admin_links"] += int(link_created)

        # 2) Create categories + services for EACH salon
        for salon in salons.values():
            for sort_order, (cat_title, services) in enumerate(categories_services, start=1):
                cat, was_created = ServiceCategory.objects.get_or_create(
                    salon=salon,
                    title=cat_title,
                    defaults={"sort_order": sort_order, "is_active": True},
                )
                changed = False
                if cat.sort_order != sort_order:
                    cat.sort_order = sort_order
                    changed = True
                if not cat.is_active:
                    cat.is_active = True
                    changed = True
                if changed:
                    cat.save(update_fields=["sort_order", "is_active"])

                created["categories"] += int(was_created)

                for service_title, price_str in services:
                    svc, was_created = Service.objects.get_or_create(
                        salon=salon,
                        category=cat,
                        title=service_title,
                        defaults={
                            "price": _money_to_int(price_str),
                            "duration_minutes": 60,
                            "is_active": True,
                        },
                    )
                    price_int = _money_to_int(price_str)
                    svc_changed = False
                    if svc.price != price_int:
                        svc.price = price_int
                        svc_changed = True
                    if not svc.is_active:
                        svc.is_active = True
                        svc_changed = True
                    if svc.duration_minutes <= 0:
                        svc.duration_minutes = 60
                        svc_changed = True
                    if svc_changed:
                        svc.save(update_fields=["price", "duration_minutes", "is_active"])

                    created["services"] += int(was_created)

        # 3) Create masters
        for salon_name, names in masters_by_salon.items():
            salon = salons.get(salon_name)
            if not salon:
                continue

            for name in names:
                name = (name or "").strip()
                if not name or name.lower() == "любой мастер":
                    continue

                m, was_created = Master.objects.get_or_create(
                    salon=salon,
                    name=name,
                    defaults={"is_active": True},
                )
                if not m.is_active:
                    m.is_active = True
                    m.save(update_fields=["is_active"])

                created["masters"] += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            "Seed done.\n"
            f"Created salons: {created['salons']}\n"
            f"Created admin users: {created['admin_users']}\n"
            f"Created admin links: {created['admin_links']}\n"
            f"Created categories: {created['categories']}\n"
            f"Created services: {created['services']}\n"
            f"Created masters: {created['masters']}\n"
            "\nSalon admins for PM testing:\n"
            "BeautyCity Пушкинская — +79990000001\n"
            "BeautyCity Ленина — +79990000002\n"
            "BeautyCity Красная — +79990000003\n",
        ))
