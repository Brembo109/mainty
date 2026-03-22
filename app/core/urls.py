from django.urls import path

from .views import AdminDemoView, DashboardView, EditorDemoView, HomeView


app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("editor/", EditorDemoView.as_view(), name="editor-demo"),
    path("admin-area/", AdminDemoView.as_view(), name="admin-demo"),
]
