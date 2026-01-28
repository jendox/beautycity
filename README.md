# BeautyCity

Учебный проект на Django: сайт сети салонов красоты с записью на услуги.

## Возможности

- Лендинг (`/`): список салонов, популярных услуг и мастеров.
- Запись на услугу (`/service/`): выбор салона/услуги/мастера, подбор доступных слотов, удержание слота (hold).
- Промокоды (скидка в процентах).
- Авторизация по телефону + OTP-код (DRF + сессии).
- Личный кабинет клиента (`/cabinet/`): ближайшие и прошедшие записи, сумма неоплаченных.
- Кабинет администратора салона (`/salon-admin/`) и стандартная Django-admin (`/admin/`).

## Технологии

- Python 3.13
- Django 5.2 + Django REST Framework
- PostgreSQL 16
- `uv` (управление зависимостями), `ruff`, `pre-commit`
- Прод: Docker Compose + Gunicorn + Caddy (HTTPS, раздача `/static/` и `/media/`)

## Быстрый старт (локальная разработка)

### Зависимости

- Python `3.13.*`
- `uv`
- Docker + Docker Compose

### Конфигурация

Скопируйте пример окружения:

```bash
cp .env.example .env
```

Важно: переменные `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` обязательны (они читаются в `config/settings.py` без значений по умолчанию).

### Запуск PostgreSQL

```bash
docker compose -f docker-compose.develop.yml up -d
```

Альтернатива через `Makefile`:

```bash
make up-develop
```

### Установка зависимостей и запуск Django

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo_data
uv run python manage.py runserver
```

Сайт будет доступен на `http://127.0.0.1:8000/`.

## Демо-данные

Команда `python manage.py seed_demo_data` создаёт демо-салоны/услуги/мастеров/смены, промокоды и пользователей-администраторов салона:

- BeautyCity Пушкинская — `+79990000001`
- BeautyCity Ленина — `+79990000002`
- BeautyCity Красная — `+79990000003`

## Полезные команды

Запуск/остановка PostgreSQL:

```bash
make up-develop
make down-develop
make down-v # с очисткой volumes
```

Линтер/форматирование:

```bash
make lint
make format
```

Миграции/админ:

```bash
make migrate
make admin # создание админа (alias to: python manage.py createsuperuser)
```

Pre-commit хуки:

```bash
uv run pre-commit install
```

## HTTP маршруты

### Web

- `/` — главная
- `/service/` — запись на услугу
- `/service/confirm/` — финальный экран подтверждения
- `/cabinet/` — кабинет клиента
- `/salon-admin/` — кабинет администратора салона
- `/admin/` — Django admin

### API

Салоны/услуги/мастера:

- `GET /api/salons/`
- `GET /api/salons/<salon_id>/services/`
- `GET /api/salons/<salon_id>/masters/`
- `GET /api/masters/`
- `GET /api/masters/<master_id>/`
- `GET /api/services/<service_id>/`

Авторизация и согласие на обработку ПДн:

- `GET /api/auth/csrf/`
- `GET /api/pd/consent-required/?phone=<raw_phone>`
- `POST /api/pd/consent/`
- `POST /api/auth/request-code/`
- `POST /api/auth/verify-code/`
- `POST /api/auth/logout/`

Запись/слоты:

- `GET /api/availability/dates/`
- `GET /api/availability/slots/`
- `GET /api/masters/<master_id>/availability/`
- `POST /api/booking/holds/`
- `GET|DELETE /api/booking/holds/<hold_id>/`
- `POST /api/booking/holds/<hold_id>/apply-promo/`
- `POST /api/appointments/`
- `GET /api/me/appointments/`

## Переменные окружения

Основные (обязательные для запуска приложения):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`true/false`)
- `DJANGO_SMS_DEBUG` (`true/false`) — если `true`, OTP пишется в лог; если `false`, отправляется в Telegram
- `ALLOWED_HOSTS` — список через запятую
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

БД (можно задавать либо `DATABASE_URL`, либо набор `POSTGRES_*`):

- `DATABASE_URL`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

OTP (необязательные, есть дефолты):

- `OTP_MAX_ATTEMPTS` (по умолчанию `3`)
- `OTP_RESEND_TIMEOUT_SECONDS` (по умолчанию `60`)
- `OTP_TTL_SECONDS` (по умолчанию `300`)

Для продового Docker Compose (см. `DEPLOY.md`):

- `DOMAIN` — домен для Caddy/HTTPS
- `MEDIA_DIR` — путь на хосте для хранения `media/`
- `IMAGE_REPO`, `IMAGE_TAG` — если используется `docker-compose.prod.hub.yml`

## Деплой

Инструкции по деплою на VPS (Docker Compose + Caddy/HTTPS) находятся в `DEPLOY.md`.
