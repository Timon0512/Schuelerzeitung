from submissions.models import Submission
from .models import Article
from .site_settings import get_site_settings


def admin_branding(request):
    if not request.path.startswith("/admin/"):
        return {}
    return {
        "publication_name": get_site_settings(tolerate_database_error=True).publication_name,
        "editorial_navigation": ("Article", "Submission", "Media"),
    }


def admin_submission_notifications(request):
    """Expose the number of new submissions to the admin navigation."""
    if not request.path.startswith("/admin/") or not request.user.is_authenticated:
        return {}
    if not request.user.has_perm("submissions.view_submission"):
        return {}
    return {
        "unread_submission_count": Submission.objects.filter(status=Submission.Status.NEW).count(),
    }


def admin_work_queue(request):
    match = request.resolver_match
    if not match or match.view_name != "admin:index":
        return {}
    user = getattr(request, "user", None)
    if user is None or not user.is_active or not user.is_staff:
        return {}
    drafts = ()
    if user.has_perm("news.view_article") or user.has_perm("news.change_article"):
        drafts = Article.objects.filter(status=Article.Status.DRAFT).select_related("category").order_by("-updated_at", "-pk")[:6]
    inbox = ()
    if user.has_perm("submissions.view_submission") or user.has_perm("submissions.change_submission"):
        inbox = Submission.objects.filter(status=Submission.Status.NEW).select_related("category").order_by("-submitted_at", "-pk")[:6]
    return {"admin_drafts": drafts, "admin_inbox": inbox}
