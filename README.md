# mainty

Internal browser-based web application scaffold for managing machines, equipment, maintenance, and qualifications. This repository intentionally contains only the technical foundation for a production-oriented start with Django, PostgreSQL, Docker Compose, Nginx, and Gunicorn.

## Stack

- Python 3.12
- Django
- PostgreSQL
- Docker Compose
- Nginx
- Gunicorn
- Django Templates
- HTMX
- Bootstrap 5

## Project Structure

```text
.
|-- .env.example
|-- .gitignore
|-- Dockerfile
|-- README.md
|-- docker-compose.yml
|-- docker/
|   `-- entrypoint.sh
|-- nginx/
|   `-- default.conf
`-- app/
    |-- manage.py
    |-- gunicorn.conf.py
    |-- accounts/
    |-- config/
    |-- core/
    |-- static/
    `-- templates/
```

## Prerequisites

- Docker Engine with Compose plugin
- Access to the private repository
- A `.env` file created from `.env.example`

## Setup

1. Copy the example configuration:

   ```bash
   cp .env.example .env
   ```

2. Adjust the values in `.env`, especially:
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - PostgreSQL credentials

3. Start the containers:

   ```bash
   docker compose up -d --build
   ```

4. Migrations run automatically on container start. To create a superuser:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

5. Open the application in a browser:
   - local: `http://localhost/`
   - internal network later: use the Ubuntu VM IP or internal DNS name

## Development Notes

- Django uses server-rendered templates.
- HTMX and Bootstrap 5 are already included in the base template.
- The `core` and `accounts` apps are prepared as the foundation for future modules.
- The protected example page at `/dashboard/` requires authentication.

Useful commands:

```bash
docker compose logs -f
docker compose exec web python manage.py test
docker compose exec web python manage.py collectstatic --noinput
```

## Production-Oriented Notes

- Use `DEBUG=False` outside local development.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the correct internal hostnames or IP addresses.
- Nginx is configured as a reverse proxy in front of Gunicorn.
- Static files are provided through a shared Docker volume.
- For real deployment, add backups, monitoring, TLS for the internal network, and proper secret management.

## Intentionally Not Included Yet

- Domain models for machines, equipment, maintenance, or qualifications
- API layer
- Celery
- Audit trail
- Document management
- Role and permission model beyond the Django Auth baseline
