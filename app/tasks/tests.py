from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset

from .models import Task


class TaskModelTests(TestCase):
    def test_task_overdue_helper(self):
        task = Task.objects.create(
            title="Prepare calibration",
            due_date=timezone.localdate() - timedelta(days=1),
            status=Task.STATUS_OPEN,
        )

        self.assertTrue(task.is_overdue)

    def test_completed_at_is_cleared_for_non_done_status(self):
        task = Task(
            title="Close open task",
            status=Task.STATUS_OPEN,
            completed_at=timezone.now(),
        )

        task.full_clean()
        self.assertIsNone(task.completed_at)

    def test_completed_at_is_set_when_task_is_done(self):
        task = Task(title="Complete task", status=Task.STATUS_DONE)

        task.full_clean()

        self.assertIsNotNone(task.completed_at)

    def test_completed_at_cannot_be_in_the_future(self):
        task = Task(
            title="Future completed task",
            status=Task.STATUS_DONE,
            completed_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            task.full_clean()


class TaskViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(username="admin", password="pass-12345")
        self.editor_user = user_model.objects.create_user(username="editor", password="pass-12345")
        self.viewer_user = user_model.objects.create_user(username="viewer", password="pass-12345")
        self.assignee_user = user_model.objects.create_user(username="operator", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(
            asset_id="A-1000",
            name="Packaging Line 1",
            status=Asset.STATUS_ACTIVE,
        )
        self.task = Task.objects.create(
            title="Inspect safety guard",
            asset=self.asset,
            due_date=timezone.localdate() - timedelta(days=1),
            priority=Task.PRIORITY_HIGH,
            status=Task.STATUS_OPEN,
            responsible_user=self.assignee_user,
        )

    def test_task_list_requires_login(self):
        response = self.client.get(reverse("tasks:list"))
        expected = f"{reverse('accounts:login')}?next={reverse('tasks:list')}"
        self.assertRedirects(response, expected)

    def test_viewer_can_access_list_and_detail_but_not_edit_views(self):
        self.client.force_login(self.viewer_user)

        list_response = self.client.get(reverse("tasks:list"))
        detail_response = self.client.get(reverse("tasks:detail", args=[self.task.pk]))
        create_response = self.client.get(reverse("tasks:create"))
        edit_response = self.client.get(reverse("tasks:edit", args=[self.task.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_editor_can_create_task(self):
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("tasks:create"),
            {
                "title": "Prepare maintenance shutdown",
                "description": "Coordinate work package",
                "asset": self.asset.pk,
                "due_date": "2026-04-01",
                "priority": Task.PRIORITY_MEDIUM,
                "status": Task.STATUS_OPEN,
                "responsible_user": self.assignee_user.pk,
            },
        )

        created_task = Task.objects.get(title="Prepare maintenance shutdown")
        self.assertRedirects(response, reverse("tasks:detail", args=[created_task.pk]))
        self.assertEqual(created_task.asset, self.asset)
        self.assertEqual(created_task.responsible_user, self.assignee_user)

    def test_admin_can_create_task(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("tasks:create"),
            {
                "title": "Admin task",
                "description": "Created by admin",
                "asset": "",
                "due_date": "",
                "priority": Task.PRIORITY_LOW,
                "status": Task.STATUS_OPEN,
                "responsible_user": "",
            },
        )

        created_task = Task.objects.get(title="Admin task")
        self.assertRedirects(response, reverse("tasks:detail", args=[created_task.pk]))

    def test_admin_can_edit_task(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("tasks:edit", args=[self.task.pk]),
            {
                "title": "Inspect safety guard updated",
                "description": "Inspection completed",
                "asset": self.asset.pk,
                "due_date": "2026-04-02",
                "priority": Task.PRIORITY_LOW,
                "status": Task.STATUS_IN_PROGRESS,
                "responsible_user": self.assignee_user.pk,
            },
        )

        self.task.refresh_from_db()
        self.assertRedirects(response, reverse("tasks:detail", args=[self.task.pk]))
        self.assertEqual(self.task.title, "Inspect safety guard updated")
        self.assertEqual(self.task.status, Task.STATUS_IN_PROGRESS)

    def test_completed_at_is_set_when_marking_task_done_in_update_view(self):
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("tasks:edit", args=[self.task.pk]),
            {
                "title": self.task.title,
                "description": "",
                "asset": self.asset.pk,
                "due_date": "2026-04-03",
                "priority": Task.PRIORITY_HIGH,
                "status": Task.STATUS_DONE,
                "responsible_user": self.assignee_user.pk,
            },
        )

        self.task.refresh_from_db()
        self.assertRedirects(response, reverse("tasks:detail", args=[self.task.pk]))
        self.assertIsNotNone(self.task.completed_at)

    def test_completed_at_is_cleared_when_reopening_task(self):
        completed_task = Task.objects.create(
            title="Closed task",
            status=Task.STATUS_DONE,
        )
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("tasks:edit", args=[completed_task.pk]),
            {
                "title": completed_task.title,
                "description": "",
                "asset": "",
                "due_date": "",
                "priority": Task.PRIORITY_MEDIUM,
                "status": Task.STATUS_OPEN,
                "responsible_user": "",
            },
        )

        completed_task.refresh_from_db()
        self.assertRedirects(response, reverse("tasks:detail", args=[completed_task.pk]))
        self.assertIsNone(completed_task.completed_at)

    def test_linked_asset_tasks_are_visible_on_asset_detail(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("assets:detail", args=[self.asset.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, reverse("tasks:detail", args=[self.task.pk]))

    def test_task_list_filters_overdue_tasks(self):
        Task.objects.create(
            title="Future task",
            due_date=timezone.localdate() + timedelta(days=3),
            status=Task.STATUS_OPEN,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("tasks:list"), {"overdue": "yes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inspect safety guard")
        self.assertNotContains(response, "Future task")

    def test_task_list_can_filter_by_assignee(self):
        other_user = get_user_model().objects.create_user(username="other", password="pass-12345")
        Task.objects.create(
            title="Unassigned example",
            responsible_user=other_user,
            status=Task.STATUS_OPEN,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("tasks:list"), {"responsible_user": self.assignee_user.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertNotContains(response, "Unassigned example")

    def test_viewer_can_export_filtered_tasks(self):
        Task.objects.create(
            title="Closed task",
            asset=self.asset,
            due_date=timezone.localdate() - timedelta(days=5),
            priority=Task.PRIORITY_LOW,
            status=Task.STATUS_DONE,
        )
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("tasks:list"), {"overdue": "yes", "export": "csv"})

        content = response.content.decode("utf-8-sig")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Inspect safety guard", content)
        self.assertNotIn("Closed task", content)
