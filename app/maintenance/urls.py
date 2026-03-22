from django.urls import path

from .views import (
    MaintenanceEventCreateView,
    MaintenanceEventUpdateView,
    MaintenancePlanCreateView,
    MaintenancePlanDetailView,
    MaintenancePlanListView,
    MaintenancePlanUpdateView,
)


app_name = "maintenance"

urlpatterns = [
    path("plans/", MaintenancePlanListView.as_view(), name="plan-list"),
    path("plans/create/", MaintenancePlanCreateView.as_view(), name="plan-create"),
    path("plans/<int:pk>/", MaintenancePlanDetailView.as_view(), name="plan-detail"),
    path("plans/<int:pk>/edit/", MaintenancePlanUpdateView.as_view(), name="plan-edit"),
    path("plans/<int:plan_pk>/events/create/", MaintenanceEventCreateView.as_view(), name="event-create"),
    path("events/<int:pk>/edit/", MaintenanceEventUpdateView.as_view(), name="event-edit"),
]
