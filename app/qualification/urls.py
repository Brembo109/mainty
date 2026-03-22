from django.urls import path

from .views import (
    QualificationEventCreateView,
    QualificationEventUpdateView,
    QualificationPlanCreateView,
    QualificationPlanDetailView,
    QualificationPlanListView,
    QualificationPlanUpdateView,
)


app_name = "qualification"

urlpatterns = [
    path("plans/", QualificationPlanListView.as_view(), name="plan-list"),
    path("plans/create/", QualificationPlanCreateView.as_view(), name="plan-create"),
    path("plans/<int:pk>/", QualificationPlanDetailView.as_view(), name="plan-detail"),
    path("plans/<int:pk>/edit/", QualificationPlanUpdateView.as_view(), name="plan-edit"),
    path("plans/<int:plan_pk>/events/create/", QualificationEventCreateView.as_view(), name="event-create"),
    path("events/<int:pk>/edit/", QualificationEventUpdateView.as_view(), name="event-edit"),
]
