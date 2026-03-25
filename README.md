# mainty

> Disclaimer: This project was entirely vibecoded with Codex.

Internal browser-based Django application for managing assets, maintenance, qualification cycles, maintenance/service contracts, operational tasks, internal users, administratively managed system defaults, practical list exports, traceable audit history, configurable company branding, reverse-proxy aware access settings, and role/permission assignments on top of Django Groups. The repository provides a production-oriented setup with PostgreSQL, Docker, Nginx, Gunicorn, role-based access, a dashboard, media handling, and a read-only audit trail.

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
- Assets, maintenance, qualification, tasks, dashboard, audit trail, system settings, exports, and branding

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
    |-- contracts/
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
- The `core`, `accounts`, `assets`, `contracts`, `maintenance`, `qualification`, `tasks`, and `audit` apps are active parts of the application.
- The protected pages `/dashboard/`, `/settings/`, `/audit/`, `/editor/`, `/admin-area/`, and `/accounts/profile/` demonstrate role checks and internal navigation.
- Domain data models are available in Django admin for internal maintenance of master data.
- The UI uses shared template helpers for consistent badges, filters, pagination, and detail-page layout.
- Global defaults for new maintenance and qualification plans are managed through the regular mainty UI and remain overridable per plan.
- Branding is split into a fixed Mainty app logo and an optional company logo managed through system settings.

## Current Functional Scope

- Authentication with login/logout
- Role-based access with `Admin`, `User`, and `Viewer`
- Admin-managed user administration in the regular mainty UI
- Admin-managed role/permission matrix for Mainty-relevant Django group permissions
- Dashboard as main landing page after login
- Admin-managed system settings for default maintenance and qualification plan values
- Admin-managed network/access settings for reverse proxy operation
- Admin-managed optional company logo for header and login page branding
- CRUD for:
  - assets
  - maintenance and service contracts with multi-asset assignment
  - maintenance plans and events
  - qualification plans and events
  - tasks
- Filter-aware CSV and XLSX exports for assets, maintenance plans, qualification plans, tasks, and audit log
- Global audit trail and object-specific change history
- Contract status visualization in contract lists, contract details, asset lists, asset details, and dashboard widgets
- Audit logging for system settings changes
- German UI with i18n-ready structure
- Shared status badges, filter layout, pagination, detail-page structure, and branded header/login layout across modules

## Roles and Permissions

The application uses Django authentication together with Django Groups and linked user profiles for the authorization layer:

- `Admin`: full access, including user administration, permission management, and administrative system settings.
- `User`: access to internal operational pages and write-capable module flows.
- `Viewer`: access to internal read-only pages.

Implementation notes:

- Role checks are enforced server-side through reusable mixins in `accounts.mixins`.
- Role helper functions live in `accounts.roles`.
- User-specific metadata such as `Kürzel` and role assignment are stored in `accounts.UserProfile`.
- The regular UI exposes `/accounts/users/` for user administration and `/accounts/permissions/` for the role-permission matrix.
- Navigation visibility is only a convenience layer. Access control is enforced in the views.
- The `bootstrap_roles` management command creates the initial groups and applies the Mainty default permission set.

Useful commands:

```bash
docker compose logs -f
docker compose exec web python manage.py test
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py bootstrap_roles
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

## Contract Module

The `Verträge` module manages maintenance and service contracts as a dedicated entity instead of storing contract data directly on assets.

- A contract can be linked to one or many assets.
- An asset can be linked to multiple contracts.
- Contracts store title, contract number, order number, vendor, start date, end date, warning period in months, maintenance frequency, notes, and linked assets.
- Contract changes and asset assignment changes are included in the existing audit trail.

### Contract Status Logic

Contract status is calculated dynamically from the current date and the configured warning period for each contract:

- `Aktiv`: contract end date is outside the warning period
- `Läuft bald aus`: contract is still active but the end date falls within the configured warning period
- `Abgelaufen`: contract end date is in the past

No manual status field is maintained.

### Warning Periods

Each contract has its own `Vorwarnzeit` in months. This value determines when the contract changes from `Aktiv` to `Läuft bald aus`.

Examples:

- `3` months for short commercial service contracts
- `6` months for annual review contracts
- `12` months for long-running service agreements with longer procurement lead times

### Where Contract Status Is Visible

Contract status and remaining runtime are shown in multiple places:

- `Verträge` list with filters, sorting, exports, status badge, and remaining runtime
- contract detail page with linked assets and audit history
- asset overview through a compact colored contract indicator
- asset detail page in the linked contracts section
- dashboard widgets for expiring and expired contracts

## Production-Oriented Notes

- Use `DEBUG=False` outside local development.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the correct internal hostnames or IP addresses.
- `TASK_DASHBOARD_WARNING_DAYS` controls how many days in advance open tasks are shown in the dashboard warning section.
- Maintenance and qualification plan creation use admin-managed defaults from `/settings/`; changing these defaults only affects future records.
- Uploaded company logos are stored as media files and served through Django in development and Nginx in the current Docker setup.
- User and role-permission management is available in the regular mainty UI for `Admin` users and remains backed by Django Groups and Permissions.
- Reverse-proxy relevant application settings can be managed in `/settings/`, including public URL, allowed hosts, CSRF trusted origins, HTTPS enforcement, and debug mode.
- Nginx is configured as a reverse proxy in front of Gunicorn.
- Static files and uploaded media files are provided through shared Docker volumes.
- For real deployment, add backups, monitoring, TLS for the internal network, and proper secret management.
- Use explicit role assignment after user creation. Authentication alone does not grant internal access.
- Audit entries are intentionally read-only and exposed through both Django admin and the application UI.
- Audit entries include readable user snapshots with name, `Kürzel`, and role label where available.

## Reverse Proxy / Cloudflare Tunnel

Mainty can be configured behind a reverse proxy such as Cloudflare Tunnel, but the tunnel itself remains an external infrastructure component.

Configure in Mainty:

- `/settings/`:
  - `Öffentliche URL`
  - `Allowed Hosts`
  - `CSRF Trusted Origins`
  - `HTTPS erzwingen`
  - `Debug-Modus`

Configure outside Mainty:

- Cloudflare Tunnel creation and lifecycle
- DNS routing
- Access policies
- TLS/certificate handling on the Cloudflare side
- restart/redeploy of the Mainty containers after changing proxy-relevant settings

Important:

- Mainty evaluates `X-Forwarded-Proto` for reverse-proxy HTTPS detection.
- Changes to network/access settings are stored in the database and audited, but they still require an application restart to be applied consistently across the running stack.

## Intentionally Not Included Yet

- API layer
- Celery
- Document management
- Notifications / reminder jobs
