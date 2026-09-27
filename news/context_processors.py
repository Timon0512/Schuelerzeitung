from submissions.models import Submission


def admin_submission_notifications(request):
    """Expose the number of new submissions to the admin navigation."""
    if not request.path.startswith("/admin/") or not request.user.is_authenticated:
        return {}
    if not request.user.has_perm("submissions.view_submission"):
        return {}
    return {
        "unread_submission_count": Submission.objects.filter(status=Submission.Status.NEW).count(),
    }
