from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from news.models import Media, content_lock
from news.image_variants import VARIANT_FIELDS, attach_variants, delete_files, encode_variants


class Command(BaseCommand):
    help = "Bildvarianten prüfen; mit --execute fehlende Varianten erzeugen. Ausgangsdateien bleiben erhalten."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        count = errors = original_bytes = web_bytes = small_bytes = 0
        for pk in Media.objects.order_by("pk").values_list("pk", flat=True).iterator():
            created = []
            try:
                with transaction.atomic():
                    # Serialize against editorial file replacements, including source reads.
                    content_lock()
                    media = Media.objects.filter(pk=pk).first()
                    if media is None or (media.small_file and media.large_file):
                        continue
                    with media.file.open("rb") as source:
                        encoded = encode_variants(source)
                    old = [(f.storage, f.name) for f in (media.small_file, media.large_file) if f]
                    if options["execute"]:
                        attach_variants(media, encoded, created)
                        media.save(update_fields=VARIANT_FIELDS)
                        transaction.on_commit(lambda files=old: delete_files(files), robust=True)
                    count += 1
                    original_bytes += media.size
                    web_bytes += encoded["large"][0].size
                    small_bytes += encoded["small"][0].size
            except Exception as exc:
                delete_files(created)
                errors += 1
                self.stderr.write(f"Bild {pk}: {type(exc).__name__}; Verarbeitung fehlgeschlagen.")
        verb = "Verarbeitet" if options["execute"] else "Vorschau (keine Änderungen)"
        self.stdout.write(f"{verb}: {count} Bilder; Ausgangsdateien {original_bytes} Bytes; kleine Webvarianten {small_bytes} Bytes; große Webvarianten {web_bytes} Bytes; Fehler {errors}.")
        if errors:
            raise CommandError("Nicht alle Bilder konnten verarbeitet werden; erneuter Lauf setzt bei fehlenden Varianten fort.")
