from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import MaintyLoginView, ProfileView


app_name = "accounts"

urlpatterns = [
    path("login/", MaintyLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
