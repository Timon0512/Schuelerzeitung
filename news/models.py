import uuid
from pathlib import Path
from .content import clean_body
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction, connection
from django.db.models import Q
from django.utils import timezone
from django.utils.html import strip_tags


def public_article_q(prefix="", at=None):
    return Q(**{prefix + "status": "published", prefix + "published_at__lte": at or timezone.now()})


def content_lock():
    # One transaction-scoped lock also serializes the initially empty table.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [52431003])


class Category(models.Model):
    name = models.CharField("Name", max_length=80)
    slug = models.SlugField(unique=True)
    color = models.CharField("Farbe", max_length=7, default="#B84318", validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$")])
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Rubrik"
        verbose_name_plural = "Rubriken"

    def __str__(self):
        return self.name


class AuthorQuerySet(models.QuerySet):
    def public(self):
        return self.filter(public_article_q("articles__"), is_public=True).distinct()


class Author(models.Model):
    display_name = models.CharField("Anzeigename", max_length=120)
    slug = models.SlugField(unique=True)
    bio = models.TextField("Kurzbeschreibung", blank=True, max_length=2000)
    is_public = models.BooleanField("Öffentlich freigegeben", default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    objects = AuthorQuerySet.as_manager()

    class Meta:
        verbose_name = "Autorendarstellung"
        verbose_name_plural = "Autorendarstellungen"

    def __str__(self):
        return self.display_name


def media_path(instance, filename):
    return f"images/{uuid.uuid4().hex}/image{Path(filename).suffix.lower()}"


class MediaQuerySet(models.QuerySet):
    def public(self):
        return self.filter(public_article_q("hero_articles__") | public_article_q("placements__article__")).distinct()


class Media(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField("Datei", upload_to=media_path)
    alt_text = models.CharField("Alternativtext", max_length=300, blank=True)
    caption = models.CharField("Bildunterschrift", max_length=500, blank=True)
    mime_type = models.CharField("Dateityp", max_length=30, choices=[(x, x) for x in ("image/jpeg", "image/png", "image/webp")])
    width = models.PositiveIntegerField("Breite")
    height = models.PositiveIntegerField("Höhe")
    size = models.PositiveIntegerField("Dateigröße")
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    objects = MediaQuerySet.as_manager()

    def __str__(self):
        return self.alt_text or "Bild ohne Alternativtext"

    class Meta:
        verbose_name = "Bild"
        verbose_name_plural = "Bilder"
        constraints = [
            models.CheckConstraint(condition=Q(width__gt=0, height__gt=0, size__gt=0, size__lte=10485760), name="media_positive_bounded_size"),
            models.CheckConstraint(condition=models.lookups.LessThanOrEqual(models.F("width") * models.F("height"), 25000000), name="media_max_pixels"),
            models.CheckConstraint(condition=Q(mime_type__in=["image/jpeg", "image/png", "image/webp"]), name="media_image_types"),
        ]


class ArticleQuerySet(models.QuerySet):
    def public(self):
        return self.filter(public_article_q())

    def lead(self):
        return self.public().order_by("-featured", "-published_at", "-pk").first()


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Entwurf"
        PUBLISHED = "published", "Veröffentlicht"
        ARCHIVED = "archived", "Archiviert"

    title = models.CharField("Titel", max_length=240)
    slug = models.SlugField(unique=True, max_length=240)
    excerpt = models.TextField("Teaser", max_length=600, blank=True)
    body = models.TextField("Artikeltext", blank=True)
    body_text = models.TextField(editable=False, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Rubrik")
    author = models.ForeignKey(Author, null=True, blank=True, on_delete=models.PROTECT, related_name="articles")
    hero_image = models.ForeignKey(Media, null=True, blank=True, on_delete=models.PROTECT, related_name="hero_articles")
    status = models.CharField("Status", max_length=12, choices=Status, default=Status.DRAFT)
    published_at = models.DateTimeField("Veröffentlichungsdatum", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField("Aufmacher", default=False)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    images = models.ManyToManyField(Media, through="ArticleMedia", related_name="articles")
    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-pk"]
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
        permissions = [("can_publish_article", "Darf Artikel veröffentlichen und Aufmacher wählen")]
        indexes = [models.Index(fields=["status", "-published_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(status__in=["draft", "published", "archived"]), name="article_valid_status"),
            models.CheckConstraint(condition=~Q(status="published") | Q(published_at__isnull=False), name="published_has_date"),
            models.CheckConstraint(condition=Q(featured=False) | Q(status="published"), name="featured_is_published"),
            models.UniqueConstraint(fields=["featured"], condition=Q(featured=True), name="one_featured_article"),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            content_lock()
            previous = type(self).objects.filter(pk=self.pk).first() if self.pk else None
            # Partial writes must not create redirects for a slug that was not saved.
            if kwargs.get("update_fields") is not None and "slug" not in kwargs["update_fields"] and previous:
                self.slug = previous.slug
            if SlugRedirect.objects.filter(slug=self.slug).exclude(article_id=self.pk).exists():
                raise ValidationError({"slug": "Diese Adresse ist als Weiterleitung reserviert."})
            if previous and previous.published_at:
                self.published_at = previous.published_at
            if self.status == self.Status.PUBLISHED and self.published_at is None:
                self.published_at = timezone.now()
            if self.status != self.Status.PUBLISHED:
                self.featured = False
            images = getattr(self, "_allowed_images", None)
            if images is None:
                images = self.images.all() if self.pk else ()
            self.body = clean_body(self.body, images)
            self.body_text = strip_tags(self.body)
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"published_at", "featured", "body", "body_text"}
            super().save(*args, **kwargs)
            if previous and previous.published_at and previous.slug != self.slug:
                SlugRedirect.objects.get_or_create(slug=previous.slug, defaults={"article": self})
            SlugRedirect.objects.filter(slug=self.slug, article=self).delete()

    def __str__(self):
        return self.title


class ArticleMedia(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="image_placements")
    media = models.ForeignKey(Media, on_delete=models.PROTECT, related_name="placements")
    position = models.PositiveIntegerField(default=0)
    caption = models.CharField("Bildunterschrift", max_length=500, blank=True)

    class Meta:
        ordering = ["position", "pk"]
        constraints = [models.UniqueConstraint(fields=["article", "media"], name="unique_article_media")]


class SlugRedirect(models.Model):
    slug = models.SlugField(unique=True, max_length=240)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="redirects")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            content_lock()
            if Article.objects.filter(slug=self.slug).exists():
                raise ValidationError("Eine aktive Artikeladresse darf keine Weiterleitung sein.")
            return super().save(*args, **kwargs)


class SiteSetting(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    publication_name = models.CharField("Zeitungsname", max_length=80, default="KAKTUS")
    tagline = models.CharField("Untertitel", max_length=200, blank=True)
    school_name = models.CharField("Schule", max_length=160, default="Aggertal-Gymnasium")
    logo = models.ForeignKey(Media, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Zeitungseinstellung"
        verbose_name_plural = "Zeitungseinstellungen"
        constraints = [models.CheckConstraint(condition=Q(id=1), name="single_site_setting")]
