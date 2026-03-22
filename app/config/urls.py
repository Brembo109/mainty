from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("assets/", include("assets.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("qualification/", include("qualification.urls")),
    path("tasks/", include("tasks.urls")),
]
