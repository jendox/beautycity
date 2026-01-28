# Деплой BeautyCity (Docker Compose + VPS)

В репозитории есть «производственный» деплой через Docker Compose:

- `web`: Django + Gunicorn
- `postgres`: PostgreSQL 16
- `caddy`: HTTPS (Let's Encrypt), reverse proxy, раздача `/static/` и `/media/`

## Требования

- VPS на Ubuntu 24.04 с публичным IP.
- Домен с A-записью: `<YOUR_DOMAIN> -> <VPS_IP>`.
- Открытые порты: `80/tcp` и `443/tcp`.

## Установка Docker на VPS

```bash
sudo apt update
sudo apt -y install ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
```

Перезайдите по SSH (или выполните `newgrp docker`) и проверьте:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

## Размещение проекта на VPS

Рекомендуемая структура:

- `/opt/beautycity/app` — репозиторий (git checkout)
- `/opt/beautycity/media` — постоянное хранилище пользовательских загрузок

```bash
sudo mkdir -p /opt/beautycity
sudo chown -R $USER:$USER /opt/beautycity
mkdir -p /opt/beautycity/media

cd /opt/beautycity
git clone <YOUR_REPO_URL> app
cd /opt/beautycity/app
```

## Продовый `.env`

Создайте `/opt/beautycity/app/.env` (файл игнорируется через `.gitignore`, в репозиторий добавлять не нужно).

Минимальный пример:

```env
DOMAIN=<YOUR_DOMAIN>
MEDIA_DIR=/opt/beautycity/media

DJANGO_DEBUG=false
DJANGO_SECRET_KEY=PASTE_A_LONG_RANDOM_SECRET_KEY
ALLOWED_HOSTS=<YOUR_DOMAIN>

DJANGO_SMS_DEBUG=true
TELEGRAM_BOT_TOKEN=PASTE_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=-123456789

POSTGRES_DB=beautycity
POSTGRES_USER=beautycity_user
POSTGRES_PASSWORD=PASTE_STRONG_PASSWORD
DATABASE_URL=postgres://beautycity_user:PASTE_STRONG_PASSWORD@postgres:5432/beautycity

OTP_MAX_ATTEMPTS=3
OTP_RESEND_TIMEOUT_SECONDS=60
OTP_TTL_SECONDS=300
```

Примечания:

- Значения лучше хранить без кавычек (без `'...'`).
- `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` обязательны: они читаются в `config/settings.py` без значений по умолчанию.
- Если `DJANGO_SMS_DEBUG=false`, OTP отправляется в Telegram; если `true` — OTP пишется в лог (но переменные `TELEGRAM_*` всё равно должны быть заданы).

## Запуск контейнеров (сборка на VPS)

```bash
cd /opt/beautycity/app
docker compose -f docker-compose.prod.yml up -d --build
```

Полезно для отладки:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -n 200 postgres
docker compose -f docker-compose.prod.yml logs -n 200 web
docker compose -f docker-compose.prod.yml logs -n 200 caddy
```

## Миграции и статика

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

Опционально (для учебного стенда): заполнить БД демо-данными (салоны/услуги/мастера/смены/промокоды).

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py seed_demo_data
```

## Создание администратора

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Обновление деплоя

```bash
cd /opt/beautycity/app
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Альтернатива: Docker Hub образ

Плюс этого подхода: VPS не собирает образ, а только скачивает готовый.

### Секреты для GitHub Actions

В настройках репозитория GitHub добавьте secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (access token Docker Hub с правами push)

Workflow: `.github/workflows/docker-publish.yml`.

### Когда публикуется образ

- Push в `main` публикует:
  - `jendox/beautycity:latest`
  - `jendox/beautycity:sha-<shortsha>`
- Теги вида `v1.2.3` публикуют `jendox/beautycity:v1.2.3`

### Деплой на VPS из Docker Hub

Используйте `docker-compose.prod.hub.yml` вместо `docker-compose.prod.yml`:

```bash
cd /opt/beautycity/app
docker compose -f docker-compose.prod.hub.yml pull
docker compose -f docker-compose.prod.hub.yml up -d
docker compose -f docker-compose.prod.hub.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.hub.yml exec web python manage.py collectstatic --noinput
```

Если вы публикуете образ не в `jendox/beautycity`, укажите в `/opt/beautycity/app/.env`:

```env
IMAGE_REPO=<YOUR_DOCKERHUB_USERNAME>/<YOUR_IMAGE_NAME>
```

Чтобы зафиксировать конкретную сборку, задайте в `/opt/beautycity/app/.env`:

```env
IMAGE_TAG=sha-<shortsha>
```

## Частые проблемы

- HTTPS не поднимается: проверьте, что A-запись домена уже указывает на VPS, и порты `80/443` доступны снаружи; затем посмотрите `docker compose -f docker-compose.prod.yml logs -n 200 caddy`.
- `/static/` не отдаётся: выполните `collectstatic` (Caddy раздаёт статику из volume `staticfiles`, он пустой до `collectstatic`).
