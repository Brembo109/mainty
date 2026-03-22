from .models import SystemSettings


def branding_context(request):
    settings = SystemSettings.load()
    return {
        "app_logo_static_path": "img/mainty-logo.svg",
        "company_logo": settings.company_logo,
    }
