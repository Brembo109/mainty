from django.urls import path

from .views import (
    MaintenanceContractCreateView,
    MaintenanceContractDeleteView,
    MaintenanceContractDetailView,
    MaintenanceContractListView,
    MaintenanceContractUpdateView,
)


app_name = "contracts"

urlpatterns = [
    path("", MaintenanceContractListView.as_view(), name="list"),
    path("create/", MaintenanceContractCreateView.as_view(), name="create"),
    path("<int:pk>/", MaintenanceContractDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", MaintenanceContractUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", MaintenanceContractDeleteView.as_view(), name="delete"),
]
