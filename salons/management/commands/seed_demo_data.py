from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from salons.models import Master, Salon, SalonAdmin, Service, ServiceCategory

User = get_user_model()


def _money_to_int(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0


def _set_filefield_from_static(*, filefield, dst_name: str, src_path: Path) -> bool:
    if not src_path.exists():
        return False

    expected_name = dst_name
    if filefield:
        try:
            expected_name = filefield.field.generate_filename(filefield.instance, dst_name)
        except Exception:
            expected_name = dst_name

    if filefield and filefield.name == expected_name:
        return False

    try:
        storage = filefield.storage
        if storage.exists(expected_name):
            storage.delete(expected_name)
    except Exception:
        pass

    try:
        if filefield:
            filefield.delete(save=False)
    except Exception:
        pass

    with src_path.open("rb") as fp:
        filefield.save(dst_name, File(fp), save=True)
    return True


class Command(BaseCommand):
    help = "Seed demo data (salons, admins, categories, services, masters) from frontend templates"

    @transaction.atomic
    def handle(self, *args, **options):
        static_root = Path(settings.BASE_DIR) / "static"

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
            "salon_images": 0,
            "service_images": 0,
            "master_images": 0,
        }

        # Create / update salons
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

        salon_images = {
            "BeautyCity Пушкинская": static_root / "img" / "salons" / "salon1.svg",
            "BeautyCity Ленина": static_root / "img" / "salons" / "salon2.svg",
            "BeautyCity Красная": static_root / "img" / "salons" / "salon3.svg",
        }
        for salon_name, src_path in salon_images.items():
            salon = salons.get(salon_name)
            if not salon:
                continue
            dst_name = f"demo_{salon.id}.svg"
            if _set_filefield_from_static(filefield=salon.image, dst_name=dst_name, src_path=src_path):
                created["salon_images"] += 1

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

        # Create categories + services for EACH salon
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

        service_images = [
            static_root / "img" / "services" / "service1.svg",
            static_root / "img" / "services" / "service2.svg",
            static_root / "img" / "services" / "service3.svg",
            static_root / "img" / "services" / "service4.svg",
            static_root / "img" / "services" / "service5.svg",
            static_root / "img" / "services" / "service6.svg",
        ]
        for salon in salons.values():
            salon_services = list(Service.objects.filter(salon=salon).order_by("id"))
            for idx, svc in enumerate(salon_services, start=1):
                src_path = service_images[(idx - 1) % len(service_images)]
                dst_name = f"demo_{salon.id}_{idx}.svg"
                if _set_filefield_from_static(filefield=svc.image, dst_name=dst_name, src_path=src_path):
                    created["service_images"] += 1

        # Create masters
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

        master_images = [
            static_root / "img" / "masters" / "master1.svg",
            static_root / "img" / "masters" / "master2.svg",
            static_root / "img" / "masters" / "master3.svg",
            static_root / "img" / "masters" / "master4.svg",
            static_root / "img" / "masters" / "master5.svg",
            static_root / "img" / "masters" / "master6.svg",
        ]
        for salon_name, names in masters_by_salon.items():
            salon = salons.get(salon_name)
            if not salon:
                continue
            if not hasattr(Master, "image"):
                continue

            for idx, name in enumerate(names, start=1):
                name = (name or "").strip()
                if not name or name.lower() == "любой мастер":
                    continue
                try:
                    master = Master.objects.get(salon=salon, name=name)
                except Master.DoesNotExist:
                    continue
                src_path = master_images[(idx - 1) % len(master_images)]
                dst_name = f"demo_{salon.id}_{idx}.svg"
                if _set_filefield_from_static(filefield=master.image, dst_name=dst_name, src_path=src_path):
                    created["master_images"] += 1

        # Booking demo data (promo codes + shifts)
        try:
            from datetime import time as dtime

            from appointments.models import MasterShift, PromoCode
        except Exception:
            MasterShift = None  # type: ignore[assignment]
            PromoCode = None  # type: ignore[assignment]

        if PromoCode is not None:
            promo_payload = [
                ("kid20", 20),
                ("birthday", 15),
                ("man10", 10),
            ]
            for code, percent in promo_payload:
                PromoCode.objects.update_or_create(
                    code=code,
                    defaults={"discount_percent": percent, "is_active": True, "valid_from": None, "valid_to": None},
                )

        if MasterShift is not None:
            work_start = dtime(hour=10, minute=0)
            work_end = dtime(hour=20, minute=0)
            weekdays = range(0, 7)
            for master in Master.objects.filter(is_active=True).select_related("salon"):
                for wd in weekdays:
                    MasterShift.objects.update_or_create(
                        master=master,
                        salon=master.salon,
                        weekday=wd,
                        defaults={"starts_time": work_start, "ends_time": work_end, "is_active": True},
                    )

        self.stdout.write(self.style.SUCCESS(
            "Seed done.\n"
            f"Created salons: {created['salons']}\n"
            f"Created admin users: {created['admin_users']}\n"
            f"Created admin links: {created['admin_links']}\n"
            f"Created categories: {created['categories']}\n"
            f"Created services: {created['services']}\n"
            f"Created masters: {created['masters']}\n"
            f"Attached salon images: {created['salon_images']}\n"
            f"Attached service images: {created['service_images']}\n"
            f"Attached master images: {created['master_images']}\n"
            "\nSalon admins for PM testing:\n"
            "BeautyCity Пушкинская — +79990000001\n"
            "BeautyCity Ленина — +79990000002\n"
            "BeautyCity Красная — +79990000003\n",
        ))
