# mainty

Interne browserbasierte Webanwendung als Grundgeruest fuer die Verwaltung von Maschinen, Anlagen, Wartungen und Qualifizierungen. Dieses Repository enthaelt bewusst nur das technische Setup fuer einen produktionsnahen Start mit Django, PostgreSQL, Docker Compose, Nginx und Gunicorn.

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

## Projektstruktur

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

## Voraussetzungen

- Docker Engine mit Compose Plugin
- Zugriff auf das private Repository
- Eine `.env` Datei auf Basis von `.env.example`

## Setup

1. Beispielkonfiguration kopieren:

   ```bash
   cp .env.example .env
   ```

2. Werte in `.env` anpassen, insbesondere:
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - PostgreSQL Zugangsdaten

3. Container starten:

   ```bash
   docker compose up -d --build
   ```

4. Migrationen laufen beim Start automatisch. Fuer einen Superuser:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

5. Anwendung im Browser oeffnen:
   - lokal: `http://localhost/`
   - intern spaeter mit der IP oder dem DNS-Namen der Ubuntu-VM

## Entwicklung

- Django nutzt serverseitig gerenderte Templates.
- HTMX und Bootstrap 5 sind bereits im Base-Template eingebunden.
- Die Apps `core` und `accounts` sind als Basis fuer weitere Module vorbereitet.
- Die geschuetzte Beispielseite `/dashboard/` erfordert einen Login.

Nuetzliche Befehle:

```bash
docker compose logs -f
docker compose exec web python manage.py test
docker compose exec web python manage.py collectstatic --noinput
```

## Produktionsnahe Hinweise

- `DEBUG=False` ausserhalb lokaler Entwicklung verwenden.
- `ALLOWED_HOSTS` und `CSRF_TRUSTED_ORIGINS` sauber auf interne Hostnamen oder IPs setzen.
- Das Nginx-Setup dient als Reverse Proxy vor Gunicorn.
- Statische Dateien werden ueber ein gemeinsames Docker-Volume bereitgestellt.
- Fuer echtes Deployment sollten Backups, Monitoring, TLS im internen Netz und Secrets-Management ergaenzt werden.

## Noch bewusst nicht enthalten

- Fachmodelle fuer Maschinen, Anlagen, Wartungen oder Qualifizierungen
- API
- Celery
- Audittrail
- Dokumentenverwaltung
- Rollen- und Rechtemodell jenseits von Django Auth Basisfunktionen
