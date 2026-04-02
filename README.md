# mainty

Browser-based maintenance management system for tracking assets, maintenance plans, qualification cycles, and service contracts.

Built with Django, PostgreSQL, and Docker. Designed for internal deployment behind a reverse proxy.

---

## Requirements

- Docker and Docker Compose
- A configured `.env` file (see below)
- A reverse proxy (Nginx, Caddy, or Cloudflare Tunnel)

---

## Quick Start

```bash
cp .env.example .env
# Edit .env with your settings

docker compose up -d --build
docker compose exec web python manage.py bootstrap_roles
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py create_initial_admin
```

The application is then available at `http://localhost` (or your configured domain).

---

## Configuration

All configuration is done via environment variables in `.env`.

### Required

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (generate a random string) |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins (e.g. `https://mainty.example.com`) |

### Email (required for reminders)

| Variable | Description | Default |
|---|---|---|
| `EMAIL_HOST` | SMTP server hostname | -- |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Enable TLS | `true` |
| `EMAIL_HOST_USER` | SMTP username | -- |
| `EMAIL_HOST_PASSWORD` | SMTP password | -- |
| `DEFAULT_FROM_EMAIL` | Sender address | `noreply@mainty.local` |

### Optional

| Variable | Description | Default |
|---|---|---|
| `DEBUG` | Enable debug mode | `false` |
| `SESSION_COOKIE_AGE` | Session lifetime in seconds | `3600` |
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `false` |
| `SESSION_COOKIE_SECURE` | Secure session cookie | `true` |
| `AXES_FAILURE_LIMIT` | Failed login attempts before lockout | `5` |
| `AXES_COOLOFF_TIME` | Lockout duration in minutes | `15` |

---

## Reminders

Reminders are sent via Django management commands. Schedule these with cron or a similar tool:

```bash
# Daily: send reminders for due and overdue items
docker compose exec -T web python manage.py send_due_reminders

# Daily digest
docker compose exec -T web python manage.py send_digest_notifications --frequency daily

# Weekly digest (run on your preferred weekday)
docker compose exec -T web python manage.py send_digest_notifications --frequency weekly
```

Example crontab:

```
0 7 * * *   docker compose -f /opt/mainty/docker-compose.yml exec -T web python manage.py send_due_reminders
0 7 * * *   docker compose -f /opt/mainty/docker-compose.yml exec -T web python manage.py send_digest_notifications --frequency daily
0 7 * * 1   docker compose -f /opt/mainty/docker-compose.yml exec -T web python manage.py send_digest_notifications --frequency weekly
```

---

## Roles

| Role | Access |
|---|---|
| Admin | Full access including user and system management |
| User | Operational access (create, edit records) |
| Viewer | Read-only access |

Roles are assigned per user in the admin area. The role system is enforced server-side.

---

## Production Checklist

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` set to a strong random value
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` configured for your domain
- [ ] HTTPS enabled via reverse proxy
- [ ] Email credentials configured and tested
- [ ] Reminder commands scheduled via cron
- [ ] PostgreSQL data directory backed up regularly
- [ ] Monitoring in place (health check at `/health/` or equivalent)
