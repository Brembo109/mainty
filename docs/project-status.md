# Project Status

`mainty` is currently set up as a browser-based internal Django application with a production-oriented infrastructure foundation. The repository already includes Docker Compose, PostgreSQL, Nginx, Gunicorn, Django Templates, Bootstrap 5, and prepared HTMX integration. The application is running on the internal Ubuntu VM and is reachable through the browser.

The current implementation now covers the technical platform, the authentication/authorization baseline, the initial domain model foundation, a production-oriented internal dashboard, a central audit trail, an administrative system settings area, filter-aware operational exports, configurable branding with company logo support, a cross-module UX consistency layer, and server-rendered CRUD UI for assets, maintenance plans/events, qualification plans/events, and operational tasks. Document workflows are not implemented yet.

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
- Admin-only system settings page in the regular mainty UI
- Fixed Mainty app logo in header and login page
- Optional company logo upload in the regular mainty UI
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
- Singleton-style `SystemSettings` model for application-wide defaults
- Admin-managed default values for new maintenance plans:
  - warning days
  - interval value
  - interval unit
- Admin-managed default values for new qualification plans:
  - warning days
  - interval value
  - interval unit
- Prefilled maintenance and qualification plan create forms using the current system settings
- Independent per-record persistence after form submission, so later settings changes do not modify existing plans
- Media-backed company logo setting with:
  - optional upload via `/settings/`
  - preview in the settings UI
  - display in the login page
  - display in the top application header
  - audit coverage through the existing system settings tracking
- Filter-aware CSV and XLSX exports for:
  - assets
  - maintenance plans
  - qualification plans
  - tasks
  - audit log
- Central audit trail with:
  - dedicated `audit` app
  - global `/audit/` page with filters, search, and pagination
  - object-specific change history on asset, maintenance plan, qualification plan, and task detail pages
  - field-level change logging with old and new values
  - user attribution from the request context
  - action types for create, update, delete, and status changes
  - optional `change_reason` field prepared for later form integration
  - read-only Django admin integration
  - logging of system settings create/update changes
- Cross-module UX refinement with:
  - unified status badges for assets, due-statuses, tasks, dashboard, and audit-related UI
  - consistent list filter layout, reset behavior, and active-filter highlighting
  - shared pagination and result-meta template fragments
  - consistent table spacing, action button patterns, and empty states
  - active navigation highlighting for the current module
  - improved detail-page structure and status presentation
  - two-row header layout with separated account area and module navigation
  - branding-aware login page and header presentation
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
  - standardized search, filtering, sorting, pagination
  - unified asset status badges
  - server-side permission checks for Admin / Editor / Viewer
- Maintenance UI with:
  - maintenance plan list
  - maintenance plan detail page
  - create and update maintenance plans
  - create and update maintenance events
  - due-status transparency in list/detail views
  - unified overdue/warning row highlighting and badge styling
  - linked maintenance sections on the asset detail page
- Qualification UI with:
  - qualification plan list
  - qualification plan detail page
  - create and update qualification plans
  - create and update qualification events
  - due-status transparency in list/detail views
  - unified overdue/warning row highlighting and badge styling
  - linked qualification sections on the asset detail page
- Task UI with:
  - task list
  - task detail page
  - create and update tasks
  - standardized search, filtering, sorting, pagination
  - overdue visibility and completion-state handling
  - unified task status badges and row emphasis
  - linked task section on the asset detail page
- Environment-based cookie security settings for the current internal HTTP phase and later HTTPS switch-over
- Shared Docker/Nginx media handling for uploaded company branding files

## Authorization Model

The current authorization model is intentionally simple and Django-native.

- `Admin`
  - full access
  - intended for user management and administrative settings
- `Editor`
  - access to internal operational pages
  - intended for future create/edit workflows in business modules
- `Viewer`
  - access to internal read-only areas
  - no edit capabilities

Navigation visibility adapts to the signed-in user, but access control is enforced server-side in the views.

All three roles can access the operational dashboard in read-only form.
All three roles can also access the audit trail in read-only form.
Only `Admin` can access and update `/settings/`.

## Domain Model Status

The following domain apps and models are already present:

- `audit`
  - `AuditLog`
- `assets`
  - `Asset`
- `core`
  - `SystemSettings`
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

The audit layer additionally provides:

- field-level tracking of relevant model changes
- indexed log storage for model/object lookup and chronological filtering
- request-aware user attribution through middleware
- reusable object-level query helpers for detail pages

The shared UX layer additionally provides:

- reusable template helpers for status badges and active navigation state
- reusable list metadata and pagination includes
- common table/filter styling in the shared stylesheet
- consistent scanability for list, detail, dashboard, and audit pages
- a two-row branded top area with fixed app branding and optional company branding

The export layer additionally provides:

- reusable CSV/XLSX response helpers
- filter-aware exports from the existing list querysets
- German column labels and timestamped filenames

The currently implemented business UI layers are:

- internal dashboard
- system settings
- audit trail
- assets
- maintenance plans and maintenance events
- qualification plans and qualification events
- operational tasks
- operational list exports

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
    |   |-- context_processors.py
    |   |-- due_dates.py
    |   |-- dashboard.py
    |   |-- exports.py
    |   |-- forms.py
    |   |-- intervals.py
    |   |-- ui.py
    |   |-- templatetags/
    |   |   `-- mainty_ui.py
    |   |-- migrations/
    |   |   `-- 0001_initial.py
    |   |   `-- 0002_systemsettings_company_logo.py
    |   |-- tests.py
    |   |-- urls.py
    |   `-- views.py
    |-- audit/
    |   |-- admin.py
    |   |-- apps.py
    |   |-- context.py
    |   |-- middleware.py
    |   |-- models.py
    |   |-- registry.py
    |   |-- services.py
    |   |-- signals.py
    |   |-- tests.py
    |   |-- urls.py
    |   |-- views.py
    |   |-- migrations/
    |   |   `-- 0001_initial.py
    |   `-- templatetags/
    |       `-- audit_ui.py
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
    |   |   |-- form_field.html
    |   |   |-- list_meta.html
    |   |   `-- pagination.html
    |   |-- audit/
    |   |   |-- audit_list.html
    |   |   `-- partials/
    |   |       `-- object_history.html
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
    |       |-- settings_form.html
    |       |-- home.html
    |       |-- dashboard.html
    |       |-- editor_demo.html
    |       `-- admin_demo.html
    `-- static/
        |-- css/app.css
        `-- img/mainty-logo.svg
```

## What Is Not Implemented Yet

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
- `c8d8add` Add audit trail system
- `101319e` Refine UI consistency and docs
- `2b01f07` Adjust README disclaimer language
- `eb33267` Add system settings defaults
- `94df36c` Add filtered list exports
