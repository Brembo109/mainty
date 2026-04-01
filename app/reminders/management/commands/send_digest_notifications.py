from django.core.management.base import BaseCommand, CommandError

from reminders.services import send_digest_notifications


class Command(BaseCommand):
    help = "Sendet tägliche oder wöchentliche Digest-Benachrichtigungen."

    def add_arguments(self, parser):
        parser.add_argument("--frequency", choices=["daily", "weekly"], default="daily")
        parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, was gesendet würde.")

    def handle(self, *args, **options):
        frequency = options["frequency"]
        if frequency not in {"daily", "weekly"}:
            raise CommandError("Ungültige Frequenz.")
        result = send_digest_notifications(frequency=frequency, dry_run=options["dry_run"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Digest {frequency}: sent={result['sent']} skipped={result['skipped']} failed={result['failed']}"
            )
        )
