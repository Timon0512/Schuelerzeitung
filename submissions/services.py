import uuid
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify
from news.models import Article, content_lock
from news.services import require_editor
from .models import Submission
from django.views.decorators.debug import sensitive_variables


@sensitive_variables()
def receive_submission(form):
    """Only accept a validated form; clean up storage if the database write fails."""
    if not form.is_valid():
        raise ValueError("Ungültiges Formular")
    from news.models import Media
    data = form.cleaned_data
    media = None
    try:
        with transaction.atomic():
            if data.get("image"):
                file, width, height = data["image"]
                media = Media(file=file, width=width, height=height, size=file.size,
                              mime_type="image/webp", submission_origin=True)
                media.save()
            return Submission.objects.create(**{key: data[key] for key in (
                "name", "class_level", "title", "category", "body", "authorship_confirmed")}, image=media)
    except Exception:
        if media is not None and media.file.name and media.file._committed:
            from news.image_variants import delete_files, stored_files
            delete_files(stored_files(media))
        raise


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
