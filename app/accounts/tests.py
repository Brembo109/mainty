from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog

from accounts.permissions import assign_default_role_permissions, build_permissions_matrix
from accounts.roles import ROLE_ADMIN, ROLE_USER, ROLE_VIEWER


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="strong-pass-123",
        )
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)
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


class UserManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.user_group, _ = Group.objects.get_or_create(name=ROLE_USER)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(
            username="admin",
            password="pass-12345",
            first_name="Marc",
            last_name="Heyer",
        )
        self.regular_user = user_model.objects.create_user(
            username="user1",
            password="pass-12345",
        )
        self.viewer_user = user_model.objects.create_user(
            username="viewer1",
            password="pass-12345",
        )

        self.admin_user.groups.add(self.admin_group)
        self.regular_user.groups.add(self.user_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.admin_user.profile.user_code = "MH"
        self.admin_user.profile.role = ROLE_ADMIN
        self.admin_user.profile.save()

    def test_admin_can_access_user_management_views(self):
        self.client.force_login(self.admin_user)

        list_response = self.client.get(reverse("accounts:user-list"))
        create_response = self.client.get(reverse("accounts:user-create"))
        edit_response = self.client.get(reverse("accounts:user-edit", args=[self.viewer_user.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(edit_response.status_code, 200)

    def test_non_admin_users_cannot_access_user_management_views(self):
        for user in (self.regular_user, self.viewer_user):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("accounts:user-list")).status_code, 403)
            self.assertEqual(self.client.get(reverse("accounts:user-create")).status_code, 403)
            self.assertEqual(
                self.client.get(reverse("accounts:user-edit", args=[self.admin_user.pk])).status_code,
                403,
            )

    def test_creating_user_creates_profile_and_role(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:user-create"),
            {
                "username": "abecker",
                "first_name": "Anna",
                "last_name": "Becker",
                "email": "anna@example.com",
                "user_code": "AB",
                "role": ROLE_USER,
                "is_active": "on",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
            },
        )

        self.assertRedirects(response, reverse("accounts:user-list"))
        created_user = get_user_model().objects.get(username="abecker")
        self.assertEqual(created_user.profile.user_code, "AB")
        self.assertEqual(created_user.profile.role, ROLE_USER)
        self.assertTrue(created_user.groups.filter(name=ROLE_USER).exists())

    def test_role_changes_are_persisted(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("accounts:user-edit", args=[self.viewer_user.pk]),
            {
                "username": self.viewer_user.username,
                "first_name": "Anna",
                "last_name": "Becker",
                "email": "anna.becker@example.com",
                "user_code": "AB",
                "role": ROLE_USER,
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:user-edit", args=[self.viewer_user.pk]))
        self.viewer_user.refresh_from_db()
        self.assertEqual(self.viewer_user.profile.role, ROLE_USER)
        self.assertEqual(self.viewer_user.profile.user_code, "AB")
        self.assertTrue(self.viewer_user.groups.filter(name=ROLE_USER).exists())

    def test_audit_display_uses_user_code_and_role_snapshot(self):
        self.client.force_login(self.admin_user)
        self.client.post(
            reverse("accounts:user-create"),
            {
                "username": "nview",
                "first_name": "Nina",
                "last_name": "View",
                "email": "nina@example.com",
                "user_code": "NV",
                "role": ROLE_VIEWER,
                "is_active": "on",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
            },
        )

        audit_entry = AuditLog.objects.filter(model_name="User").latest("id")
        self.assertIn("Marc Heyer [MH]", audit_entry.user_display)
        self.assertIn("Admin", audit_entry.user_display)

    def test_audit_snapshot_remains_readable_after_user_profile_changes(self):
        self.client.force_login(self.admin_user)
        self.client.post(
            reverse("accounts:user-create"),
            {
                "username": "snapshot",
                "first_name": "Snapshot",
                "last_name": "User",
                "email": "snapshot@example.com",
                "user_code": "SU",
                "role": ROLE_VIEWER,
                "is_active": "on",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
            },
        )

        audit_entry = AuditLog.objects.filter(model_name="User").latest("id")
        self.admin_user.first_name = "Maria"
        self.admin_user.last_name = "Mueller"
        self.admin_user.save()
        self.admin_user.profile.user_code = "MM"
        self.admin_user.profile.save()

        self.assertIn("Marc Heyer [MH]", audit_entry.user_display)
        self.assertIn("Admin", audit_entry.user_display)


class PermissionMatrixTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.user_group, _ = Group.objects.get_or_create(name=ROLE_USER)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)
        assign_default_role_permissions()

        self.admin_user = user_model.objects.create_user(
            username="admin",
            password="pass-12345",
            first_name="Marc",
            last_name="Heyer",
        )
        self.regular_user = user_model.objects.create_user(
            username="user1",
            password="pass-12345",
        )
        self.viewer_user = user_model.objects.create_user(
            username="viewer1",
            password="pass-12345",
        )

        self.admin_user.groups.add(self.admin_group)
        self.regular_user.groups.add(self.user_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.admin_user.profile.user_code = "MH"
        self.admin_user.profile.role = ROLE_ADMIN
        self.admin_user.profile.save()

    def _matrix_post_data(self, **overrides):
        data = {}
        for section in build_permissions_matrix():
            for row in section["rows"]:
                for role_state in row["role_states"]:
                    if role_state["enabled"]:
                        data[f"perm__{row['key']}__{role_state['name']}"] = "on"
        data.update(overrides)
        return data

    def test_permissions_matrix_requires_admin(self):
        for user in (self.regular_user, self.viewer_user):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("accounts:permission-matrix")).status_code, 403)

    def test_permissions_matrix_renders_for_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("accounts:permission-matrix"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geräte anzeigen")
        self.assertContains(response, "Wartung")
        self.assertContains(response, "Rollen & Rechte")

    def test_matrix_changes_update_group_permissions(self):
        self.client.force_login(self.admin_user)
        permission = Permission.objects.get(content_type__app_label="assets", codename="add_asset")
        self.viewer_group.permissions.remove(permission)

        response = self.client.post(
            reverse("accounts:permission-matrix"),
            self._matrix_post_data(perm__assets_add__Viewer="on"),
        )

        self.assertRedirects(response, reverse("accounts:permission-matrix"))
        self.viewer_group.refresh_from_db()
        self.assertTrue(self.viewer_group.permissions.filter(pk=permission.pk).exists())

    def test_matrix_changes_create_audit_entries(self):
        self.client.force_login(self.admin_user)
        permission = Permission.objects.get(content_type__app_label="tasks", codename="add_task")
        self.viewer_group.permissions.remove(permission)

        self.client.post(
            reverse("accounts:permission-matrix"),
            self._matrix_post_data(perm__tasks_add__Viewer="on"),
        )

        audit_entry = AuditLog.objects.filter(model_name="Rolle", object_id=str(self.viewer_group.pk)).latest("id")
        self.assertEqual(audit_entry.field_name, "Maßnahmen anlegen")
        self.assertEqual(audit_entry.new_value, "Ja")
        self.assertIn("Marc Heyer [MH]", audit_entry.user_display)
        self.assertIn("Admin", audit_entry.user_display)

    def test_non_admin_cannot_update_permissions(self):
        self.client.force_login(self.regular_user)
        permission = Permission.objects.get(content_type__app_label="assets", codename="add_asset")

        response = self.client.post(
            reverse("accounts:permission-matrix"),
            self._matrix_post_data(perm__assets_add__Viewer="on"),
        )

        self.assertEqual(response.status_code, 403)
        self.viewer_group.refresh_from_db()
        self.assertFalse(self.viewer_group.permissions.filter(pk=permission.pk).exists())
