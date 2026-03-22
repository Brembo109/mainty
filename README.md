# mainty

> Disclaimer: This project was entirely vibecoded with Codex.

Internal browser-based Django application for managing assets, maintenance, qualification cycles, operational tasks, and traceable audit history. The repository provides a production-oriented setup with PostgreSQL, Docker, Nginx, Gunicorn, role-based access, a dashboard, and a read-only audit trail.

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
- Assets, maintenance, qualification, tasks, dashboard, and audit trail

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
    |-- audit/
    |-- manage.py
    |-- gunicorn.conf.py
    |-- accounts/
    |-- assets/
    |-- config/
    |-- core/
    |-- maintenance/
    |-- qualification/
    |-- static/
    |-- tasks/
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
- The `core`, `accounts`, `assets`, `maintenance`, `qualification`, `tasks`, and `audit` apps are active parts of the application.
- The protected pages `/dashboard/`, `/audit/`, `/editor/`, `/admin-area/`, and `/accounts/profile/` demonstrate role checks and internal navigation.
- Domain data models are available in Django admin for internal maintenance of master data.
- The UI uses shared template helpers for consistent badges, filters, pagination, and detail-page layout.

## Current Functional Scope

- Authentication with login/logout
- Role-based access with `Admin`, `Editor`, and `Viewer`
- Dashboard as main landing page after login
- CRUD for:
  - assets
  - maintenance plans and events
  - qualification plans and events
  - tasks
- Global audit trail and object-specific change history
- German UI with i18n-ready structure
- Shared status badges, filter layout, pagination, and detail-page structure across modules

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
- Audit entries are intentionally read-only and exposed through both Django admin and the application UI.

## Intentionally Not Included Yet

- API layer
- Celery
- Document management
- Notifications / reminder jobs
- Export functionality
