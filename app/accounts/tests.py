from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="strong-pass-123",
        )
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)
        self.user.groups.add(self.viewer_group)

    def test_login_page_returns_ok(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_works_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "tester", "password": "strong-pass-123"},
        )
        self.assertRedirects(response, reverse("core:dashboard"))

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        login_url = reverse("accounts:login")
        expected_target = f"{login_url}?next={reverse('accounts:profile')}"
        self.assertRedirects(response, expected_target)

    def test_profile_shows_role_information(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ROLE_VIEWER)
