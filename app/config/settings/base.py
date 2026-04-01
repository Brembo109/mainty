import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(key: str, default: str | None = None) -> str:
    return os.environ.get(key, default or "")


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    value = env(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = env("SECRET_KEY", "unsafe-development-key")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost,http://127.0.0.1",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "audit",
    "core",
    "accounts",
    "assets",
    "contracts",
    "maintenance",
    "qualification",
    "reminders",
    "tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "core.middleware.DynamicAppSettingsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "audit.middleware.AuditContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.role_context",
                "core.context_processors.branding_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "mainty"),
        "USER": env("POSTGRES_USER", "mainty"),
        "PASSWORD": env("POSTGRES_PASSWORD", "mainty"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de"
LANGUAGES = [
    ("de", _("Deutsch")),
    ("en", _("English")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:home"
TASK_DASHBOARD_WARNING_DAYS = int(env("TASK_DASHBOARD_WARNING_DAYS", "7"))
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "noreply@mainty.local")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_AGE = int(env("SESSION_COOKIE_AGE", "3600"))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
