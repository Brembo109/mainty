# mainty

Internal browser-based web application scaffold for managing machines, equipment, maintenance, and qualifications. This repository currently provides the technical foundation for a production-oriented Django setup together with a first server-side authentication and authorization model.

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
- Django Groups based role model
- Domain model foundation for assets, maintenance, qualification, and tasks

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
   - `TASK_DASHBOARD_WARNING_DAYS` for the task warning horizon shown on the dashboard
   - PostgreSQL credentials

3. Start the containers:

   ```bash
   docker compose up -d --build
   ```

4. Create the initial mainty roles:

   ```bash
   docker compose exec web python manage.py bootstrap_roles
   ```

5. Migrations run automatically on container start. To create a superuser:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. Assign the Admin role to the first administrative user:

   ```bash
   docker compose exec web python manage.py create_initial_admin \
     --username admin \
     --email admin@example.com \
     --password "change-me"
   ```

7. Open the application in a browser:
   - local: `http://localhost/`
   - internal network later: use the Ubuntu VM IP or internal DNS name

## Development Notes

- Django uses server-rendered templates.
- HTMX and Bootstrap 5 are already included in the base template.
- The `core`, `accounts`, `assets`, `maintenance`, `qualification`, and `tasks` apps are prepared as the foundation for future modules.
- The protected example pages `/dashboard/`, `/editor/`, `/admin-area/`, and `/accounts/profile/` demonstrate the role checks.
- Domain data models are available in Django admin for internal maintenance of master data.

## Roles and Permissions

The application uses Django authentication together with Django Groups for the first authorization layer:

- `Admin`: full access, including user-management related capabilities and future administrative configuration.
- `Editor`: access to internal operational pages and future write-capable module flows.
- `Viewer`: access to internal read-only pages.

Implementation notes:

- Role checks are enforced server-side through reusable mixins in `accounts.mixins`.
- Role helper functions live in `accounts.roles`.
- Navigation visibility is only a convenience layer. Access control is enforced in the views.
- The `bootstrap_roles` management command creates the initial groups.

Useful commands:

```bash
docker compose logs -f
docker compose exec web python manage.py test
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py bootstrap_roles
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

## Production-Oriented Notes

- Use `DEBUG=False` outside local development.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the correct internal hostnames or IP addresses.
- `TASK_DASHBOARD_WARNING_DAYS` controls how many days in advance open tasks are shown in the dashboard warning section.
- Nginx is configured as a reverse proxy in front of Gunicorn.
- Static files are provided through a shared Docker volume.
- For real deployment, add backups, monitoring, TLS for the internal network, and proper secret management.
- Use explicit role assignment after user creation. Authentication alone does not grant internal access.
- Domain CRUD screens are intentionally not implemented yet. Data administration is currently handled through Django admin.

## Intentionally Not Included Yet

- Domain models for machines, equipment, maintenance, or qualifications
- API layer
- Celery
- Audit trail
- Document management
