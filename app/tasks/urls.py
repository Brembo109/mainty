from django.urls import path

from .views import TaskCreateView, TaskDetailView, TaskListView, TaskUpdateView


app_name = "tasks"

urlpatterns = [
    path("", TaskListView.as_view(), name="list"),
    path("create/", TaskCreateView.as_view(), name="create"),
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="edit"),
]
