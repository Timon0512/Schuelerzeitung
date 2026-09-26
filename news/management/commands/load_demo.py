from datetime import timedelta
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image
from news.models import Article, ArticleMedia, Author, Category, Media, SiteSetting
from submissions.models import Submission


class Command(BaseCommand):
    help = "Lädt klar gekennzeichnete fiktive Demodaten wiederholbar in die Entwicklungsdatenbank."

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.ENVIRONMENT != "development" or not settings.DATABASES["default"]["NAME"].endswith(("_dev", "_test")):
            raise CommandError("Demodaten sind nur in einer *_dev- oder *_test-Datenbank erlaubt.")
        category, _ = Category.objects.get_or_create(slug="demo-rubrik", defaults={"name": "DEMO – fiktive Rubrik"})
        author, _ = Author.objects.get_or_create(slug="demo-redaktion", defaults={"display_name": "DEMO – erfundene Redaktion", "is_public": True})
        SiteSetting.objects.get_or_create(pk=1)
        for slug, status, date in [
            ("demo-artikel", "published", timezone.now() - timedelta(days=1)),
            ("demo-entwurf", "draft", None),
            ("demo-geplant", "published", timezone.now() + timedelta(days=365)),
            ("demo-archiv", "archived", None),
        ]:
            article, _ = Article.objects.get_or_create(slug=slug, defaults={
                "title": "DEMO – fiktiver Beispielbeitrag: " + slug, "category": category,
                "author": author, "status": status, "published_at": date,
                "body": "<p>Fiktive Testdaten. Keine tatsächliche Schulnachricht.</p>"})
            if not article.hero_image_id:
                article.hero_image = self.image(slug)
                article.save()
            ArticleMedia.objects.get_or_create(article=article, media=article.hero_image)
        if not Submission.objects.filter(title="DEMO – fiktive Einsendung").exists():
            Submission.objects.create(name="Erfundener Demonym", class_level="DEMO", title="DEMO – fiktive Einsendung",
                                      category=category, body="Privater fiktiver Testtext.", authorship_confirmed=True,
                                      image=self.image("private-einsendung"))
        self.stdout.write(self.style.SUCCESS("Fiktive Demodaten vorhanden; keine Konten oder Passwörter erzeugt."))

    def image(self, label):
        output = BytesIO()
        Image.new("RGB", (32, 24), "#B84318").save(output, format="PNG")
        data = output.getvalue()
        return Media.objects.create(file=ContentFile(data, name=label + ".png"), alt_text="Fiktive einfarbige Demografik",
                                    mime_type="image/png", width=32, height=24, size=len(data))
