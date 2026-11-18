from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from news.models import content_lock
from .models import Submission
from .services import convert_submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "category", "submitted_at", "name", "article_link"]
    list_filter = ["status", "category"]
    search_fields = ["title", "name"]
    fieldsets = [
        ("Beitrag", {"fields": ["title", "category", "body", "image_link"]}),
        ("Interne Angaben", {"fields": ["name", "class_level", "authorship_confirmed", "submitted_at"]}),
        ("Redaktion", {"fields": ["status", "editor_note", "article_link", "reviewed_at", "reviewed_by"]}),
    ]
    readonly_fields = ["title", "name", "class_level", "category", "body", "authorship_confirmed", "image_link", "status", "article_link", "submitted_at", "reviewed_at", "reviewed_by"]
    actions = ["convert", "review", "reject"]
    ordering = ["-submitted_at", "-pk"]
    list_select_related = ["category"]
    list_per_page = 30
    show_facets = admin.ShowFacets.NEVER
    change_form_template = "admin/submissions/submission/change_form.html"
    change_list_template = "admin/editorial_list.html"

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {**(extra_context or {}), "title": "Einsendungen"})

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        # A concurrent conversion must not be undone by saving an older note form.
        obj.save(update_fields=["editor_note"])

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = {
            **(extra_context or {}),
            "may_convert": request.user.has_perms(["submissions.change_submission", "news.change_article", "news.add_article"]),
        }
        if request.method == "POST":
            action = request.POST.get("_submission_action")
            if action and action not in {"convert", "review", "reject"}:
                raise PermissionDenied
            if action == "convert" and not extra_context["may_convert"]:
                raise PermissionDenied
            with transaction.atomic():
                content_lock()
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        action = request.POST.get("_submission_action")
        if action == "convert":
            article = convert_submission(obj.pk, user=request.user)
            self.log_change(request, obj, f"Als Entwurf übernommen: {article.pk}")
            self.message_user(request, "Die Einsendung wurde übernommen. Lege bitte die Autorendarstellung fest.")
            return redirect("admin:news_article_change", article.pk)
        if action in {"review", "reject"}:
            status = Submission.Status.IN_REVIEW if action == "review" else Submission.Status.REJECTED
            changed = self.mark(request, self.get_queryset(request).filter(pk=obj.pk), status)
            if changed:
                self.message_user(request, f"Status: {status.label}")
            return redirect("admin:submissions_submission_change", obj.pk)
        return super().response_change(request, obj)

    @admin.display(description="Entwurf")
    def article_link(self, obj):
        return format_html('<a href="{}">Artikel bearbeiten</a>', reverse("admin:news_article_change", args=[obj.article_id])) if obj.article_id else "Noch nicht übernommen"

    @admin.display(description="Eingereichtes Bild")
    def image_link(self, obj):
        if not obj.image_id:
            return "Kein Bild"
        return format_html(
            '<img class="admin-photo-preview" src="{}" alt="Eingereichtes Foto"><br><a href="{}">Bild geschützt öffnen</a>',
            reverse("private_media_variant", args=[obj.image_id, "large"]), reverse("private_media", args=[obj.image_id]),
        )

    @admin.action(description="Als Entwurf übernehmen", permissions=["change"])
    def convert(self, request, queryset):
        for submission in queryset:
            article = convert_submission(submission.pk, user=request.user)
            self.log_change(request, submission, f"Als Entwurf übernommen: {article.pk}")
        self.message_user(request, "Entwürfe sind verknüpft. Autorendarstellung bitte bewusst festlegen.")

    def mark(self, request, queryset, status):
        if not self.has_change_permission(request):
            raise PermissionDenied
        changed = False
        with transaction.atomic():
            content_lock()
            for submission in queryset.select_for_update():
                if not submission.article_id:
                    submission.status = status
                    submission.reviewed_at = timezone.now()
                    submission.reviewed_by = request.user
                    submission.save()
                    self.log_change(request, submission, submission.get_status_display())
                    changed = True
        return changed

    @admin.action(description="In Prüfung nehmen", permissions=["change"])
    def review(self, request, queryset):
        self.mark(request, queryset, Submission.Status.IN_REVIEW)

    @admin.action(description="Ablehnen", permissions=["change"])
    def reject(self, request, queryset):
        self.mark(request, queryset, Submission.Status.REJECTED)
