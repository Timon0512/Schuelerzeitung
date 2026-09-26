from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from news.models import content_lock
from .models import Submission
from .services import convert_submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["title", "name", "class_level", "status", "submitted_at", "article_link"]
    list_filter = ["status", "category"]
    search_fields = ["title", "name"]
    fields = ["title", "name", "class_level", "category", "body", "authorship_confirmed", "image_link", "status", "editor_note", "article_link", "submitted_at", "reviewed_at", "reviewed_by"]
    readonly_fields = [f for f in fields if f != "editor_note"]
    actions = ["convert", "review", "reject"]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        # A concurrent conversion must not be undone by saving an older note form.
        obj.save(update_fields=["editor_note"])

    @admin.display(description="Entwurf")
    def article_link(self, obj):
        return format_html('<a href="{}">Artikel bearbeiten</a>', reverse("admin:news_article_change", args=[obj.article_id])) if obj.article_id else "Noch nicht übernommen"

    @admin.display(description="Eingereichtes Bild")
    def image_link(self, obj):
        return format_html('<a href="{}">Bild geschützt öffnen</a>', reverse("private_media", args=[obj.image_id])) if obj.image_id else "Kein Bild"

    @admin.action(description="Als Entwurf übernehmen", permissions=["change"])
    def convert(self, request, queryset):
        for submission in queryset:
            article = convert_submission(submission.pk, user=request.user)
            self.log_change(request, submission, f"Als Entwurf übernommen: {article.pk}")
        self.message_user(request, "Entwürfe sind verknüpft. Autorendarstellung bitte bewusst festlegen.")

    def mark(self, request, queryset, status):
        if not self.has_change_permission(request):
            raise PermissionDenied
        with transaction.atomic():
            content_lock()
            for submission in queryset.select_for_update():
                if not submission.article_id:
                    submission.status = status
                    submission.reviewed_at = timezone.now()
                    submission.reviewed_by = request.user
                    submission.save()
                    self.log_change(request, submission, submission.get_status_display())

    @admin.action(description="In Prüfung nehmen", permissions=["change"])
    def review(self, request, queryset):
        self.mark(request, queryset, Submission.Status.IN_REVIEW)

    @admin.action(description="Ablehnen", permissions=["change"])
    def reject(self, request, queryset):
        self.mark(request, queryset, Submission.Status.REJECTED)
