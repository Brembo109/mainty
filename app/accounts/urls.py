from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    MaintyLoginView,
    ProfileView,
    RolePermissionMatrixView,
    UserCreateView,
    UserListView,
    UserUnlockView,
    UserUpdateView,
)


app_name = "accounts"

urlpatterns = [
    path("login/", MaintyLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user-edit"),
    path("users/<int:pk>/unlock/", UserUnlockView.as_view(), name="user-unlock"),
    path("permissions/", RolePermissionMatrixView.as_view(), name="permission-matrix"),
]
