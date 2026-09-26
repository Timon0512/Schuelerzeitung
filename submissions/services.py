import uuid
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify
from news.models import Article, content_lock
from news.services import require_editor
from .models import Submission


@transaction.atomic
def convert_submission(pk, *, user):
    require_editor(user)
    if not user.has_perms(["submissions.change_submission", "news.add_article"]):
        raise PermissionDenied
    content_lock()
    submission = Submission.objects.select_for_update().get(pk=pk)
    if submission.article_id:
        return submission.article
    article = Article.objects.create(
        title=submission.title, slug=f"{slugify(submission.title)[:190] or 'einsendung'}-{uuid.uuid4().hex}",
        category=submission.category, body="".join(f"<p>{escape(p)}</p>" for p in submission.body.splitlines() if p.strip()),
        hero_image=submission.image, editor=user,
    )
    submission.article = article
    submission.status = Submission.Status.CONVERTED
    submission.reviewed_by = user
    submission.reviewed_at = timezone.now()
    submission.save()
    return article
