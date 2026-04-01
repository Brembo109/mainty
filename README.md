# mainty

> Disclaimer: This project was entirely vibecoded with Codex.

Internal browser-based Django application for managing assets, maintenance, qualification cycles, maintenance/service contracts, operational tasks, internal users, administratively managed system defaults, practical list exports, traceable audit history, configurable company branding, reverse-proxy aware access settings, role/permission assignments on top of Django Groups, and configurable E-Mail-Erinnerungen für fällige und überfällige Wartungs- und Qualifizierungspläne. The repository provides a production-oriented setup with PostgreSQL, Docker, Nginx, Gunicorn, role-based access, a dashboard, media handling, and a read-only audit trail.

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
    |-- reminders/
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
   - optional session and login protection settings:
     - `SESSION_COOKIE_AGE` in seconds, default `3600`
     - `AXES_FAILURE_LIMIT`, default `5`
     - `AXES_COOLOFF_TIME` in minutes, default `15`
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
- Repeated UI patterns are refined around denser desktop tables, persistent filters, form sections, clearer required-field handling, and dark-mode-safe status badges.
- Global defaults for new maintenance and qualification plans are managed through the regular mainty UI and remain overridable per plan.
- Branding is split into a fixed Mainty app logo and an optional company logo managed through system settings.

## Current Functional Scope

- Authentication with login/logout
- Session handling with configurable session lifetime and browser-close session expiry
- Brute-force login protection with `django-axes`
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
- E-Mail-Erinnerungen und Digest-Benachrichtigungen für bald fällige und überfällige Wartungs- und Qualifizierungspläne
- Filter-aware CSV and XLSX exports for assets, maintenance plans, qualification plans, tasks, and audit log
- Global audit trail and object-specific change history
- Contract status visualization in contract lists, contract details, asset lists, asset details, and dashboard widgets
- Audit logging for system settings changes
- German UI with i18n-ready structure
- Shared status badges, filter layout, pagination, detail-page structure, and branded header/login layout across modules
- Focused UI/UX refinement pass for list views, forms, dashboard readability, wide-screen usage, and dark mode consistency

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

## Login Protection

Mainty protects the login view against repeated failed authentication attempts with `django-axes`.

- Default lockout threshold: `5` failed login attempts
- Default cooldown: `15` minutes
- Lockout scope: combination of `username` and `ip_address`
- Successful login resets the recorded failure counter
- Session lifetime is configurable through `SESSION_COOKIE_AGE` and defaults to `3600` seconds
- Browser sessions are configured to expire on browser close

### Admin Visibility and Unlock

The regular Mainty user administration distinguishes between two separate states:

- `Kontostatus`: Django user activation state (`Aktiv` or `Inaktiv`)
- `Loginstatus`: temporary login state managed by `django-axes` (`Login freigegeben` or `Login gesperrt`)

A locked user is not automatically set to `is_active = False`. This means a user can be active and still temporarily locked out from login after repeated failed attempts.

Admins can review the login lockout state directly in `/accounts/users/` and on the user edit page. If a user locks themselves out, an admin can clear the lockout with the built-in `Entsperren` action in the regular Mainty UI.

## Effective Permission Enforcement

Mainty uses the existing Django `Group` and `Permission` model as the effective permission source.

- The `Admin`, `User`, and `Viewer` roles are represented by Django groups.
- The permissions matrix in the regular UI assigns concrete Django permissions to those role groups.
- Application views and templates enforce these concrete permissions directly instead of relying on role names alone.
- There is no implicit application-level bypass for `Admin` or `is_superuser` users in normal Mainty views. Access is granted because the required permissions are assigned.

Backend enforcement is centralized:

- `accounts.permissions` defines the reusable permission mappings and helpers.
- `accounts.mixins.PermissionRequiredMixin` protects class-based views with a shared 403 behavior.
- `accounts.context_processors.role_context` exposes permission-derived template flags for navigation and action buttons.

Examples:

- `assets.view_asset` controls access to asset list and detail pages.
- `assets.change_asset` controls asset edit actions.
- `contracts.delete_maintenancecontract` controls contract deletion.
- `core.change_systemsettings` controls access to Mainty system settings.

When permissions are removed in the UI, the effect is immediate on the next request because the application evaluates the assigned Django permissions directly.

## Adding New Permissions

For new modules or features:

1. Add or reuse the relevant Django model permissions.
2. Add a matching row in `accounts.permissions.PERMISSION_SECTIONS`.
3. Reuse the generated permission constants or row mappings in the affected views.
4. Expose the related template visibility through `get_template_permission_context`.
5. Add view and template tests that prove the permission is enforced and not only displayed in the UI.

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

## Reminder System

Mainty includes a pragmatic first reminder implementation based on Django management commands, cron-friendly scheduling, and E-Mail delivery.

- Included objects: active maintenance plans and qualification plans
- Included states: due soon and overdue
- Notification types: upcoming reminder, overdue escalation, daily digest, weekly digest
- Delivery channel: E-Mail only in this implementation step
- Tracking: lightweight delivery log in the `reminders` app for troubleshooting and spam prevention

### Recipient Resolution

Recipients are resolved centrally:

- first by matching the `Verantwortlich` value against active users with E-Mail address
- then by users with the `User` role
- finally by users with the `Admin` role as fallback

Duplicate recipients are removed automatically. Inactive users and users without E-Mail address are ignored.

### Reminder Settings

The admin settings page includes a section `Benachrichtigungen / Erinnerungen` with:

- activation of the reminder system
- sender address
- toggles for due reminders, overdue reminders, daily digest, weekly digest
- separate lead times for maintenance and qualification
- overdue escalation threshold in days
- optional `Nur einmal pro Status benachrichtigen`

Changes to these settings are audited through the existing system settings audit trail.

### Scheduling

The first version is designed for cron or similar schedulers. Two management commands are available:

```bash
docker compose exec -T web python manage.py send_due_reminders
docker compose exec -T web python manage.py send_digest_notifications --frequency daily
docker compose exec -T web python manage.py send_digest_notifications --frequency weekly
```

Optional dry run:

```bash
docker compose exec -T web python manage.py send_due_reminders --dry-run
docker compose exec -T web python manage.py send_digest_notifications --frequency daily --dry-run
```

Typical cron approach:

- daily morning run for `send_due_reminders`
- daily run for the daily digest
- weekly run, for example every Monday, for the weekly digest

## UI / UX Refinements

The current UI layer keeps the existing Django-template architecture and Bootstrap base, but applies shared usability refinements across the main operational pages.

### Lists, Filters, and Sorting

- Main list views use a common filter bar with search, practical status filters, and sort selectors where useful.
- Active filters stay visible in the UI and are preserved in the query string.
- Frequently used filter states are persisted per list view in the browser and restored when users return to the page without a query string.
- Result meta, exports, and pagination use shared partials for consistent behavior across modules.

### Tables and Status Visualization

- Tables are tuned for higher information density on desktop screens with compact row height, sticky headers, clearer action placement, and truncation for long values.
- Statuses such as `Aktiv`, `Inaktiv`, `Fällig bald`, `Überfällig`, `Abgelaufen`, `Offen`, and `Abgeschlossen` use shared badge styles.
- Badge colors and table highlighting are designed to stay readable in light mode and dark mode.

### Forms and Required Fields

- Longer forms are grouped into consistent sections such as `Stammdaten`, `Termine und Fristen`, `Verantwortlichkeiten`, `Vertragsdaten`, and `Zusätzliche Informationen`.
- Required fields are marked consistently with `* Pflichtfeld`.
- Validation issues are surfaced directly at the affected field and additionally in a form-level alert when necessary.
- Primary and secondary actions use a shared action layout to keep `Speichern`, `Abbrechen`, `Bearbeiten`, and similar flows predictable.

### Responsive Layout and Dashboard

- The main content area uses a wider fluid container so tables and dashboard widgets make better use of larger screens.
- Dashboard tables and lists follow the same badge, truncation, and empty-state patterns as operational list views.
- The responsive behavior stays desktop-oriented, but medium laptop widths and dark mode receive explicit styling instead of fallback rendering.

### Current Limitations

- no in-app notifications yet
- no per-user preference center
- no Slack, Teams, SMS, or push integrations
- no complex escalation matrix
- responsible person matching is text-based and therefore best effort

The reminder logic is intentionally separated from transport and UI rendering so that in-app notifications can be added later without rewriting the core due-date and recipient selection logic.

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
