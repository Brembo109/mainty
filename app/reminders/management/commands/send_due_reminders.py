from django.core.management.base import BaseCommand

from reminders.services import send_due_notifications


class Command(BaseCommand):
    help = "Sendet Erinnerungen für bald fällige und überfällige Wartungs- und Qualifizierungspläne."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, was gesendet würde.")

    def handle(self, *args, **options):
        result = send_due_notifications(dry_run=options["dry_run"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Due reminders: upcoming={result['upcoming']} overdue={result['overdue']} skipped={result['skipped']} failed={result['failed']}"
            )
        )
