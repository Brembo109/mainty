from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER


class CoreViewsTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)

        self.admin_user = self.user_model.objects.create_user("admin_user", password="pass-12345")
        self.editor_user = self.user_model.objects.create_user("editor_user", password="pass-12345")
        self.viewer_user = self.user_model.objects.create_user("viewer_user", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

    def test_homepage_returns_ok(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        login_url = reverse("accounts:login")
        expected_target = f"{login_url}?next={reverse('core:dashboard')}"
        self.assertRedirects(response, expected_target)

    def test_viewer_can_access_dashboard(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_access_editor_page(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_access_admin_page(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 403)

    def test_editor_can_access_editor_page(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_access_admin_page(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_editor_page(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_admin_page(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 200)
