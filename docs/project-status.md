# Project Status

`mainty` is currently set up as a browser-based internal Django application with a production-oriented infrastructure foundation. The repository already includes Docker Compose, PostgreSQL, Nginx, Gunicorn, Django Templates, Bootstrap 5, and prepared HTMX integration. The application is running on the internal Ubuntu VM and is reachable through the browser.

The current implementation now covers the technical platform, the authentication/authorization baseline, the initial domain model foundation, a production-oriented internal dashboard, and server-rendered CRUD UI for assets, maintenance plans/events, qualification plans/events, and operational tasks. Audit trail and document workflows are not implemented yet.

## What Is Already Implemented

- Django application scaffold with modular app structure
- Docker-based runtime with separate `web`, `db`, and `nginx` services
- PostgreSQL integration
- Gunicorn application serving behind Nginx reverse proxy
- Environment-based configuration via `.env`
- Base template with Bootstrap 5 and HTMX included
- Public home page
- Login and logout using Django Auth
- Protected internal dashboard as the main authenticated entry point
- Role-based access control using Django Groups
- Three initial roles:
  - `Admin`
  - `Editor`
  - `Viewer`
- Server-side authorization checks via reusable mixins and helpers
- Example protected pages for:
  - all authenticated internal users
  - Admin + Editor only
  - Admin only
- Profile page for the logged-in user
- Django admin prepared for user/group management
- Management command to bootstrap roles
- Management command to create or update an initial admin user
- Automated tests covering authentication and role access rules
- Dashboard aggregation layer for:
  - key system metrics
  - overdue maintenance plans, qualification plans, and tasks
  - upcoming maintenance plans, qualification plans, and tasks
  - open and in-progress tasks
  - recently updated operational objects
- Configurable task warning horizon for dashboard upcoming items via `TASK_DASHBOARD_WARNING_DAYS`
- Domain model foundation for:
  - assets
  - maintenance plans and maintenance events
  - qualification plans and qualification events
  - operational tasks
- Shared due-date and due-status logic for maintenance and qualification plans
- Django admin integration for the domain models
- Asset UI with:
  - asset list
  - asset detail page
  - create asset
  - update asset
  - search, filtering, sorting, pagination
  - server-side permission checks for Admin / Editor / Viewer
- Maintenance UI with:
  - maintenance plan list
  - maintenance plan detail page
  - create and update maintenance plans
  - create and update maintenance events
  - due-status transparency in list/detail views
  - linked maintenance sections on the asset detail page
- Qualification UI with:
  - qualification plan list
  - qualification plan detail page
  - create and update qualification plans
  - create and update qualification events
  - due-status transparency in list/detail views
  - linked qualification sections on the asset detail page
- Task UI with:
  - task list
  - task detail page
  - create and update tasks
  - search, filtering, sorting, pagination
  - overdue visibility and completion-state handling
  - linked task section on the asset detail page
- Environment-based cookie security settings for the current internal HTTP phase and later HTTPS switch-over

## Authorization Model

The current authorization model is intentionally simple and Django-native.

- `Admin`
  - full access
  - intended for user management and future administrative settings
- `Editor`
  - access to internal operational pages
  - intended for future create/edit workflows in business modules
- `Viewer`
  - access to internal read-only areas
  - no edit capabilities

Navigation visibility adapts to the signed-in user, but access control is enforced server-side in the views.

All three roles can access the operational dashboard in read-only form.

## Domain Model Status

The following domain apps and models are already present:

- `assets`
  - `Asset`
- `maintenance`
  - `MaintenancePlan`
  - `MaintenanceEvent`
- `qualification`
  - `QualificationPlan`
  - `QualificationEvent`
- `tasks`
  - `Task`

These models already include:

- timestamp fields where appropriate
- Django migrations
- Django admin registration
- focused model tests
- reusable due-date helper logic for maintenance and qualification planning

The currently implemented business UI layers are:

- internal dashboard
- assets
- maintenance plans and maintenance events
- qualification plans and qualification events
- operational tasks

## Current Repository Structure

```text
mainty/
|-- .env.example
|-- .gitignore
|-- Dockerfile
|-- README.md
|-- docker-compose.yml
|-- docs/
|   `-- project-status.md
|-- docker/
|   `-- entrypoint.sh
|-- nginx/
|   `-- default.conf
`-- app/
    |-- manage.py
    |-- gunicorn.conf.py
    |-- config/
    |   |-- urls.py
    |   `-- settings/
    |       `-- base.py
    |-- core/
    |   |-- due_dates.py
    |   |-- dashboard.py
    |   |-- templatetags/
    |   |   `-- mainty_ui.py
    |   |-- tests.py
    |   |-- urls.py
    |   `-- views.py
    |-- accounts/
    |   |-- admin.py
    |   |-- context_processors.py
    |   |-- forms.py
    |   |-- mixins.py
    |   |-- roles.py
    |   |-- tests.py
    |   |-- urls.py
    |   |-- views.py
    |   `-- management/commands/
    |       |-- bootstrap_roles.py
    |       `-- create_initial_admin.py
    |-- assets/
    |   |-- admin.py
    |   |-- forms.py
    |   |-- models.py
    |   |-- tests.py
    |   |-- urls.py
    |   |-- views.py
    |   `-- templatetags/
    |       `-- assets_query.py
    |-- maintenance/
    |   |-- admin.py
    |   |-- forms.py
    |   |-- models.py
    |   |-- urls.py
    |   |-- views.py
    |   `-- tests.py
    |-- qualification/
    |   |-- admin.py
    |   |-- forms.py
    |   |-- models.py
    |   |-- urls.py
    |   |-- views.py
    |   `-- tests.py
    |-- tasks/
    |   |-- admin.py
    |   |-- forms.py
    |   |-- models.py
    |   |-- urls.py
    |   |-- views.py
    |   `-- tests.py
    |-- templates/
    |   |-- 403.html
    |   |-- base.html
    |   |-- accounts/
    |   |   |-- login.html
    |   |   `-- profile.html
    |   |-- assets/
    |   |   |-- asset_detail.html
    |   |   |-- asset_form.html
    |   |   |-- asset_list.html
    |   |   `-- partials/
    |   |       `-- field.html
    |   |-- includes/
    |   |   `-- form_field.html
    |   |-- maintenance/
    |   |   |-- event_form.html
    |   |   |-- plan_detail.html
    |   |   |-- plan_form.html
    |   |   `-- plan_list.html
    |   |-- qualification/
    |   |   |-- event_form.html
    |   |   |-- plan_detail.html
    |   |   |-- plan_form.html
    |   |   `-- plan_list.html
    |   |-- tasks/
    |   |   |-- task_detail.html
    |   |   |-- task_form.html
    |   |   `-- task_list.html
    |   `-- core/
    |       |-- home.html
    |       |-- dashboard.html
    |       |-- editor_demo.html
    |       `-- admin_demo.html
    `-- static/
        `-- css/app.css
```

## What Is Not Implemented Yet

- Audit trail
- Document management
- API layer
- Background jobs / Celery
- Notifications and scheduled jobs
- Advanced permission granularity beyond the initial role model

## Current Git Milestones

- `c248197` Initial project scaffold
- `612856c` Write documentation in English
- `eda9c1b` Add role-based access control foundation
- `7c5d6fa` Add project status documentation
- `0953d47` Add domain model foundation for operations
- `83a540a` Add asset CRUD interface
- `de31a8a` Prepare project for future i18n
- `16ddf26` Add operational dashboard
