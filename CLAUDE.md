# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mainty** is a Django-based maintenance management system (browser-based, server-rendered) for tracking assets, maintenance plans, qualification plans, service contracts, and operational tasks. It is designed for internal deployment behind a reverse proxy.

## Architecture

**Stack:** Django 5.1+, PostgreSQL 16, Gunicorn, Nginx, Docker Compose  
**Frontend:** Django templates + Bootstrap 5 + HTMX (no SPA, no JS build step)  
**Auth/AuthZ:** Django built-in auth + `django-axes` (brute-force lockout) + role-based groups (Admin, User, Viewer)

### Django Apps

All apps live under `/app/`:
- `config/` — settings (base/dev/prod split), URL root, gunicorn config
- `core/` — dashboard, system settings (singleton), shared mixins, template tags
- `accounts/` — user profiles, role management, permission matrix
- `audit/` — field-level change tracking via Django signals + middleware
- `assets/` — equipment/asset CRUD
- `maintenance/` — maintenance plans and events with due-date tracking
- `qualification/` — qualification plans and events
- `tasks/` — operational task management
- `contracts/` — service contracts
- `reminders/` — email reminder management commands

### Key Cross-Cutting Patterns

- **Audit logging**: `AuditContextMiddleware` captures request user; signals on models write to `audit.AuditLog`. Every field change is recorded.
- **Runtime settings**: `DynamicAppSettingsMiddleware` loads `core.SystemSettings` (pk=1 singleton) per request — no restart needed for most config changes.
- **Permissions**: Mixin-based (`PermissionRequiredMixin`, `RoleRequiredMixin`) on all views. Three groups — Admin, User, Viewer — bootstrapped via management command.
- **Exports**: Filter-aware CSV/XLSX exports (openpyxl) on all list views.
- **i18n**: German primary (`de`), English secondary. `LANGUAGE_CODE = 'de'`, `TIME_ZONE = 'Europe/Berlin'`.

## Common Commands

All commands run inside the Docker container:

```bash
# Start services
docker compose up -d --build

# Run migrations
docker compose exec web python manage.py migrate

# Run all tests
docker compose exec web python manage.py test

# Run tests for a single app
docker compose exec web python manage.py test maintenance

# Run a single test class or method
docker compose exec web python manage.py test maintenance.tests.MaintenancePlanTests.test_something

# Django shell
docker compose exec web python manage.py shell

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# View logs
docker compose logs -f web
```

### Initial Setup

```bash
cp .env.example .env
# Edit .env, then:
docker compose up -d --build
docker compose exec web python manage.py bootstrap_roles      # creates Admin/User/Viewer groups
docker compose exec web python manage.py create_initial_admin # creates superuser from .env vars
```

### Management Commands

```bash
# Send per-item due reminders
docker compose exec -T web python manage.py send_due_reminders

# Send digest emails
docker compose exec -T web python manage.py send_digest_notifications --frequency daily
docker compose exec -T web python manage.py send_digest_notifications --frequency weekly
```

## Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | Required for HTTPS deployments |
| `POSTGRES_*` | Database connection |
| `DJANGO_SUPERUSER_*` | Initial admin account |
| `TASK_DASHBOARD_WARNING_DAYS` | Warning threshold for task dashboard |

## URL Structure

```
/                  → core (home → dashboard redirect)
/dashboard/        → aggregated overview
/settings/         → SystemSettings (admin only)
/accounts/         → login, profiles, user management
/assets/           → asset CRUD
/maintenance/      → maintenance plans/events
/qualification/    → qualification plans/events
/tasks/            → task management
/contracts/        → service contracts
/audit/            → audit trail
/admin/            → Django admin
```

## Infrastructure Notes

- **Entrypoint** (`docker/entrypoint.sh`): runs `migrate` and `collectstatic` on every container start.
- **Nginx** (`nginx/default.conf`): proxies to `web:8000`, serves `/static/` (7-day cache) and `/media/` (1-day cache), 10 MB upload limit, passes `X-Forwarded-*` headers.
- **Gunicorn** (`app/gunicorn.conf.py`): 3 workers, 2 threads, 60s timeout, logs to stdout.
- Static and media files are shared between `web` and `nginx` via Docker volumes.
