from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from axes.models import AccessAttempt

from assets.models import Asset
from audit.models import AuditLog
from contracts.models import MaintenanceContract

from accounts.permissions import (
    PERMISSION_ROW_MAP,
    assign_default_role_permissions,
    build_permissions_matrix,
    get_permission_objects_for_row,
)
from accounts.roles import ROLE_ADMIN, ROLE_USER, ROLE_VIEWER


class LoginViewTests(TestCase):
    def setUp(self):
        assign_default_role_permissions()
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="strong-pass-123",
        )
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)
        self.user.groups.add(self.viewer_group)

    def test_login_page_returns_ok(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/i18n/setlang/"')
        self.assertContains(response, ">DE<", html=False)
        self.assertContains(response, ">EN<", html=False)
        self.assertContains(response, "data-theme-toggle")

    def test_language_switch_endpoint_redirects_and_sets_cookie(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("accounts:login")},
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

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
        assign_default_role_permissions()
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

    def _lock_user(self, user, ip_address="203.0.113.20"):
        AccessAttempt.objects.filter(username=user.username, ip_address=ip_address).delete()
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.client.post(
                reverse("accounts:login"),
                {"username": user.username, "password": "wrong-pass"},
                REMOTE_ADDR=ip_address,
            )
        return ip_address

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
            self.assertEqual(
                self.client.post(reverse("accounts:user-unlock", args=[self.admin_user.pk])).status_code,
                403,
            )

    def test_user_list_shows_lockout_status_for_locked_users(self):
        ip_address = self._lock_user(self.viewer_user)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("accounts:user-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kontostatus")
        self.assertContains(response, "Loginstatus")
        self.assertContains(response, "Login gesperrt")
        self.assertContains(response, "Entsperren")
        self.assertTrue(AccessAttempt.objects.filter(username=self.viewer_user.username, ip_address=ip_address).exists())

    def test_user_edit_shows_lockout_status_for_locked_users(self):
        self._lock_user(self.viewer_user, ip_address="203.0.113.21")
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("accounts:user-edit", args=[self.viewer_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kontostatus und Loginstatus sind getrennt")
        self.assertContains(response, "Login ist aktuell gesperrt")
        self.assertContains(response, "Benutzer entsperren")

    def test_admin_can_unlock_locked_user(self):
        ip_address = self._lock_user(self.viewer_user, ip_address="203.0.113.22")
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("accounts:user-unlock", args=[self.viewer_user.pk]),
            {"next": reverse("accounts:user-list")},
            follow=True,
        )

        self.assertRedirects(response, reverse("accounts:user-list"))
        self.assertContains(response, "Benutzer wurde entsperrt.")
        self.assertFalse(AccessAttempt.objects.filter(username=self.viewer_user.username, ip_address=ip_address).exists())

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


class PermissionEnforcementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        assign_default_role_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.user_group, _ = Group.objects.get_or_create(name=ROLE_USER)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(username="admin", password="pass-12345")
        self.regular_user = user_model.objects.create_user(username="user1", password="pass-12345")
        self.viewer_user = user_model.objects.create_user(username="viewer1", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.regular_user.groups.add(self.user_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(asset_id="A-1000", name="Packaging Line 1", status=Asset.STATUS_ACTIVE)
        self.contract = MaintenanceContract.objects.create(
            title="Servicevertrag",
            vendor="ACME Service",
            start_date="2026-01-01",
            end_date="2026-12-31",
            warning_months=3,
        )
        self.contract.assets.add(self.asset)

    def test_superuser_without_asset_view_permission_is_blocked(self):
        permission = Permission.objects.get(content_type__app_label="assets", codename="view_asset")
        self.admin_group.permissions.remove(permission)
        self.admin_user.is_superuser = True
        self.admin_user.is_staff = True
        self.admin_user.save(update_fields=["is_superuser", "is_staff"])

        self.client.force_login(self.admin_user)

        self.assertEqual(self.client.get(reverse("assets:list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("assets:detail", args=[self.asset.pk])).status_code, 403)

    def test_missing_change_permission_hides_edit_actions_and_blocks_update(self):
        permission = Permission.objects.get(content_type__app_label="assets", codename="change_asset")
        self.user_group.permissions.remove(permission)

        self.client.force_login(self.regular_user)
        detail_response = self.client.get(reverse("assets:detail", args=[self.asset.pk]))
        edit_response = self.client.get(reverse("assets:edit", args=[self.asset.pk]))

        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, "Bearbeiten")
        self.assertEqual(edit_response.status_code, 403)

    def test_missing_delete_permission_hides_delete_action_and_blocks_contract_delete(self):
        permission = Permission.objects.get(
            content_type__app_label="contracts",
            codename="delete_maintenancecontract",
        )
        self.admin_group.permissions.remove(permission)

        self.client.force_login(self.admin_user)
        detail_response = self.client.get(reverse("contracts:detail", args=[self.contract.pk]))
        delete_response = self.client.post(reverse("contracts:delete", args=[self.contract.pk]))

        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, "Löschen")
        self.assertEqual(delete_response.status_code, 403)

    def test_navigation_and_management_views_follow_matrix_permissions(self):
        self.admin_group.permissions.remove(
            *get_permission_objects_for_row(PERMISSION_ROW_MAP["users_manage"]),
            *get_permission_objects_for_row(PERMISSION_ROW_MAP["roles_manage"]),
            *get_permission_objects_for_row(PERMISSION_ROW_MAP["settings_manage"]),
            *get_permission_objects_for_row(PERMISSION_ROW_MAP["audit_view"]),
        )

        self.client.force_login(self.admin_user)
        dashboard_response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertNotContains(dashboard_response, "Benutzer")
        self.assertNotContains(dashboard_response, "Rollen & Rechte")
        self.assertNotContains(dashboard_response, "Einstellungen")
        self.assertNotContains(dashboard_response, "Audit")
        self.assertEqual(self.client.get(reverse("accounts:user-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:permission-matrix")).status_code, 403)
        self.assertEqual(self.client.get(reverse("core:settings")).status_code, 403)
        self.assertEqual(self.client.get(reverse("audit:list")).status_code, 403)

    def test_missing_audit_permission_hides_object_history(self):
        permission = Permission.objects.get(content_type__app_label="audit", codename="view_auditlog")
        self.viewer_group.permissions.remove(permission)

        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("assets:detail", args=[self.asset.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Änderungsverlauf")
        self.assertNotContains(response, "Audit Trail")
