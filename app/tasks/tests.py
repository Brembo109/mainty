from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Task


class TaskModelTests(TestCase):
    def test_task_overdue_helper(self):
        task = Task.objects.create(
            title="Prepare calibration",
            due_date=timezone.localdate() - timedelta(days=1),
            status=Task.STATUS_OPEN,
        )

        self.assertTrue(task.is_overdue)

    def test_completed_at_requires_done_status(self):
        task = Task(
            title="Close open task",
            status=Task.STATUS_OPEN,
            completed_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            task.full_clean()
