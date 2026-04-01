import ipaddress
import re
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse

from django.conf import settings as django_settings
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _


BASE_ALLOWED_HOSTS = tuple(getattr(django_settings, "ALLOWED_HOSTS", []))
BASE_CSRF_TRUSTED_ORIGINS = tuple(getattr(django_settings, "CSRF_TRUSTED_ORIGINS", []))
BASE_DEBUG = bool(getattr(django_settings, "DEBUG", False))
BASE_SECURE_SSL_REDIRECT = bool(getattr(django_settings, "SECURE_SSL_REDIRECT", False))
BASE_SESSION_COOKIE_SECURE = bool(getattr(django_settings, "SESSION_COOKIE_SECURE", False))
BASE_CSRF_COOKIE_SECURE = bool(getattr(django_settings, "CSRF_COOKIE_SECURE", False))
BASE_SECURE_PROXY_SSL_HEADER = getattr(django_settings, "SECURE_PROXY_SSL_HEADER", None)

HOSTNAME_RE = re.compile(r"^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*$")


@dataclass(frozen=True)
class AppRuntimeSettings:
    app_public_url: str
    allowed_hosts: tuple[str, ...]
    csrf_trusted_origins: tuple[str, ...]
    force_https: bool
    debug_mode: bool


def split_csv_lines(value: str) -> list[str]:
    items = []
    for chunk in (value or "").replace("\n", ",").split(","):
        item = chunk.strip()
        if item:
            items.append(item)
    return items


def normalize_allowed_hosts(value: str) -> list[str]:
    return split_csv_lines(value)


def normalize_csrf_trusted_origins(value: str) -> list[str]:
    return split_csv_lines(value)


def validate_allowed_host(value: str):
    host = value.strip()
    if host == "*":
        return

    candidate = host[1:] if host.startswith(".") else host
    if not candidate:
        raise ValueError(_("Ungültiger Hostname."))

    if candidate.lower() == "localhost":
        return

    try:
        ipaddress.ip_address(candidate.strip("[]"))
        return
    except ValueError:
        pass

    if not HOSTNAME_RE.match(candidate):
        raise ValueError(_("Ungültiger Hostname."))


def validate_csrf_origin(value: str):
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(_("Bitte eine vollständige Origin mit http:// oder https:// angeben."))
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(_("Bitte nur die Origin ohne Pfad oder Query angeben."))


@lru_cache(maxsize=1)
def get_app_settings() -> AppRuntimeSettings:
    defaults = AppRuntimeSettings(
        app_public_url="",
        allowed_hosts=BASE_ALLOWED_HOSTS,
        csrf_trusted_origins=BASE_CSRF_TRUSTED_ORIGINS,
        force_https=BASE_SECURE_SSL_REDIRECT,
        debug_mode=BASE_DEBUG,
    )

    try:
        from core.models import SystemSettings

        settings_obj = SystemSettings.objects.only(
            "app_public_url",
            "allowed_hosts",
            "csrf_trusted_origins",
            "force_https",
            "debug_mode",
        ).filter(pk=1).first()
    except (OperationalError, ProgrammingError):
        return defaults

    if settings_obj is None:
        return defaults

    allowed_hosts = tuple(normalize_allowed_hosts(settings_obj.allowed_hosts)) or BASE_ALLOWED_HOSTS
    csrf_trusted_origins = (
        tuple(normalize_csrf_trusted_origins(settings_obj.csrf_trusted_origins)) or BASE_CSRF_TRUSTED_ORIGINS
    )

    return AppRuntimeSettings(
        app_public_url=settings_obj.app_public_url,
        allowed_hosts=allowed_hosts,
        csrf_trusted_origins=csrf_trusted_origins,
        force_https=settings_obj.force_https,
        debug_mode=settings_obj.debug_mode,
    )


def clear_app_settings_cache():
    get_app_settings.cache_clear()


def apply_runtime_settings():
    app_settings = get_app_settings()
    django_settings.ALLOWED_HOSTS = list(app_settings.allowed_hosts)
    django_settings.CSRF_TRUSTED_ORIGINS = list(app_settings.csrf_trusted_origins)
    django_settings.SECURE_SSL_REDIRECT = app_settings.force_https
    django_settings.DEBUG = app_settings.debug_mode
    django_settings.SESSION_COOKIE_SECURE = True if app_settings.force_https else BASE_SESSION_COOKIE_SECURE
    django_settings.CSRF_COOKIE_SECURE = True if app_settings.force_https else BASE_CSRF_COOKIE_SECURE
    django_settings.SECURE_PROXY_SSL_HEADER = BASE_SECURE_PROXY_SSL_HEADER
    return app_settings
