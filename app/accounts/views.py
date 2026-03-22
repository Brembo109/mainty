from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

from .forms import LoginForm
from .mixins import RoleRequiredMixin
from .roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER


class MaintyLoginView(LoginView):
    authentication_form = LoginForm
    redirect_authenticated_user = True
    template_name = "accounts/login.html"


class ProfileView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
    template_name = "accounts/profile.html"
