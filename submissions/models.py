from django.conf import settings
from django.db import models
from django.db.models import Q


class Submission(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Neu"
        IN_REVIEW = "in_review", "In Prüfung"
        REJECTED = "rejected", "Abgelehnt"
        CONVERTED = "converted", "Übernommen"

    name = models.CharField("Name (intern)", max_length=120)
    class_level = models.CharField("Klasse/Jahrgang (intern)", max_length=40)
    title = models.CharField("Titel", max_length=240)
    category = models.ForeignKey("news.Category", on_delete=models.PROTECT)
    body = models.TextField("Klartext", max_length=50000)
    authorship_confirmed = models.BooleanField("Selbst geschrieben", default=False)
    image = models.ForeignKey("news.Media", null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status, default=Status.NEW)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    editor_note = models.TextField("Interne Notiz", blank=True)
    article = models.OneToOneField("news.Article", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Einsendung"
        verbose_name_plural = "Einsendungen"
        constraints = [
            models.CheckConstraint(condition=Q(status__in=["new", "in_review", "rejected", "converted"]), name="submission_valid_status"),
            models.CheckConstraint(condition=(Q(status="converted", article__isnull=False) | (~Q(status="converted") & Q(article__isnull=True))), name="converted_has_article"),
        ]
