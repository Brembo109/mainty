from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import UserProfile
from .roles import ROLE_VIEWER


User = get_user_model()


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Benutzername")
        self.fields["password"].label = _("Passwort")
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "autofocus": True,
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "current-password",
            }
        )


class UserProfileFormMixin(forms.ModelForm):
    user_code = forms.CharField(
        max_length=12,
        required=False,
        label=_("Kürzel"),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label=_("Rolle"),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {
            "username": _("Benutzername"),
            "first_name": _("Vorname"),
            "last_name": _("Nachname"),
            "email": _("E-Mail"),
            "is_active": _("Aktiv"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = getattr(self.instance, "profile", None)
        if profile is not None:
            self.fields["user_code"].initial = profile.user_code
            self.fields["role"].initial = profile.role
        else:
            self.fields["role"].initial = ROLE_VIEWER

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control" if not isinstance(field.widget, forms.Select) else "form-select"

    def clean_user_code(self):
        user_code = (self.cleaned_data.get("user_code") or "").strip().upper()
        queryset = UserProfile.objects.filter(user_code=user_code) if user_code else UserProfile.objects.none()
        if self.instance.pk:
            queryset = queryset.exclude(user=self.instance)
        if queryset.exists():
            raise forms.ValidationError(_("Dieses Kürzel ist bereits vergeben."))
        return user_code or None

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if not user.pk:
            return user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.user_code = self.cleaned_data["user_code"]
        profile.role = self.cleaned_data["role"]
        profile.save()
        return user


class UserCreateForm(UserProfileFormMixin):
    password1 = forms.CharField(
        label=_("Passwort"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta(UserProfileFormMixin.Meta):
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].initial = True

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        queryset = User.objects.filter(username__iexact=username)
        if queryset.exists():
            raise forms.ValidationError(_("Dieser Benutzername ist bereits vergeben."))
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", _("Die Passwörter stimmen nicht überein."))
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.user_code = self.cleaned_data["user_code"]
            profile.role = self.cleaned_data["role"]
            profile.save()
        return user


class UserUpdateForm(UserProfileFormMixin):
    class Meta(UserProfileFormMixin.Meta):
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        queryset = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(_("Dieser Benutzername ist bereits vergeben."))
        return username
