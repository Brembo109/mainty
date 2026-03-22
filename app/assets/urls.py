from django.urls import path

from .views import AssetCreateView, AssetDetailView, AssetListView, AssetUpdateView


app_name = "assets"

urlpatterns = [
    path("", AssetListView.as_view(), name="list"),
    path("create/", AssetCreateView.as_view(), name="create"),
    path("<int:pk>/", AssetDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", AssetUpdateView.as_view(), name="edit"),
]
