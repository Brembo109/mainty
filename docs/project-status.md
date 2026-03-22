# Project Status

`mainty` is currently set up as a browser-based internal Django application with a production-oriented infrastructure foundation. The repository already includes Docker Compose, PostgreSQL, Nginx, Gunicorn, Django Templates, Bootstrap 5, and prepared HTMX integration. The application is running on the internal Ubuntu VM and is reachable through the browser.

The current implementation intentionally focuses only on the technical platform and the authentication/authorization baseline. No domain-specific business modules for machines, equipment, maintenance, or qualifications have been implemented yet.

## What Is Already Implemented

- Django application scaffold with modular app structure
- Docker-based runtime with separate `web`, `db`, and `nginx` services
- PostgreSQL integration
- Gunicorn application serving behind Nginx reverse proxy
- Environment-based configuration via `.env`
- Base template with Bootstrap 5 and HTMX included
- Public home page
- Login and logout using Django Auth
- Protected internal dashboard
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
    |-- templates/
    |   |-- 403.html
    |   |-- base.html
    |   |-- accounts/
    |   |   |-- login.html
    |   |   `-- profile.html
    |   `-- core/
    |       |-- home.html
    |       |-- dashboard.html
    |       |-- editor_demo.html
    |       `-- admin_demo.html
    `-- static/
        `-- css/app.css
```

## What Is Not Implemented Yet

- Machine or equipment models
- Maintenance workflows
- Qualification workflows
- Audit trail
- Document management
- API layer
- Background jobs / Celery
- Advanced permission granularity beyond the initial role model

## Current Git Milestones

- `c248197` Initial project scaffold
- `612856c` Write documentation in English
- `eda9c1b` Add role-based access control foundation
