from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from news.models import Media, content_lock
from reactions.models import Reaction, RateLimitWindow
from submissions.models import Submission


class Command(BaseCommand):
    help = "Aufbewahrung prüfen; nur --execute löscht bei bestätigten Fristen. Keine Inhaltsausgabe."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        days = settings.SUBMISSION_RETENTION_DAYS
        heart_days = settings.REACTION_RETENTION_DAYS
        if options["execute"] and (not settings.RETENTION_CONFIRMED or (days <= 0 and heart_days <= 0)):
            raise CommandError("Keine bestätigte positive Aufbewahrungsfrist. Es wurde nichts gelöscht.")
        now = timezone.now()
        with transaction.atomic():
            content_lock()  # Same ordering as conversion/editorial writes.
            submissions = Submission.objects.filter(submitted_at__lt=now-timedelta(days=days)) if days > 0 else Submission.objects.none()
            reactions = Reaction.objects.filter(created_at__lt=now-timedelta(days=heart_days)) if heart_days > 0 else Reaction.objects.none()
            expired = RateLimitWindow.objects.filter(expires_at__lte=now)
            self.stdout.write(f"{'Löschung' if options['execute'] else 'Vorschau'}: {submissions.count()} Einsendungen, {reactions.count()} Herzen, {expired.count()} abgelaufene Limits.")
            media_ids = list(submissions.exclude(image=None).values_list("image_id", flat=True))
            removable = Media.objects.filter(pk__in=media_ids, hero_articles__isnull=True,
                placements__isnull=True, sitesetting__isnull=True).exclude(
                    submission__in=Submission.objects.exclude(pk__in=submissions.values("pk"))).distinct()
            self.stdout.write(f"{removable.count()} ungenutzte Einsendungsbilder werden entfernt; Artikelbilder bleiben erhalten.")
            if not options["execute"]:
                self.stdout.write("Ohne --execute keine Änderungen; Frist 0 deaktiviert die jeweilige Löschung.")
                return
            submissions.delete()
            reactions.delete()
            expired.delete()
            # Keep every image referenced by an article (including drafts), another submission or branding.
            for media in Media.objects.filter(pk__in=media_ids, submission__isnull=True,
                    hero_articles__isnull=True, placements__isnull=True, sitesetting__isnull=True).distinct():
                media.delete()
