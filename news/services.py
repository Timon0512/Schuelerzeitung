from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from .models import Article, ArticleMedia, Media, content_lock


def require_editor(user):
    if not user.is_active or not user.is_staff or not user.has_perm("news.change_article"):
        raise PermissionDenied("Die Redaktionsberechtigung fehlt.")


def selectable_media(user, article=None):
    # Submission attachments must first be explicitly converted into an article.
    if not user or not user.is_active or not user.has_perm("news.view_media"):
        return Media.objects.none()
    query = Q(uploaded_by__isnull=False, submission__isnull=True, submission_origin=False)
    if article and article.pk:
        query |= Q(placements__article=article) | Q(hero_articles=article)
    return Media.objects.filter(query).distinct()


@transaction.atomic
def save_editorial(article, *, user, images):
    require_editor(user)
    content_lock()
    previous = Article.objects.filter(pk=article.pk).first() if article.pk else None
    if previous and previous.status == Article.Status.PUBLISHED:
        require_publisher(user)
    if not previous and not user.has_perm("news.add_article"):
        raise PermissionDenied
    if article.status != (previous.status if previous else Article.Status.DRAFT):
        raise PermissionDenied("Statuswechsel nur über die Veröffentlichungsaktionen.")
    if article.featured != (previous.featured if previous else False):
        raise PermissionDenied
    images = list(images)
    ids = {image.pk for image in images}
    if article.hero_image_id:
        ids.add(article.hero_image_id)
    if set(selectable_media(user, previous).filter(pk__in=ids).values_list("pk", flat=True)) != ids:
        raise ValidationError("Ein Bild ist für diesen Artikel nicht freigegeben.")
    if article.status == Article.Status.PUBLISHED:
        if not article.author_id or any(not image.alt_text.strip() for image in Media.objects.filter(pk__in=ids)):
            raise ValidationError("Autorendarstellung und Alternativtexte sind erforderlich.")
    article.editor = user
    article._allowed_images = images
    article.save()
    ArticleMedia.objects.filter(article=article).exclude(media_id__in=[i.pk for i in images]).delete()
    for position, image in enumerate(images):
        ArticleMedia.objects.update_or_create(article=article, media=image, defaults={"position": position, "caption": image.caption})
    return article


def require_publisher(user):
    if not user.is_active or not user.has_perm("news.can_publish_article"):
        raise PermissionDenied("Die Berechtigung zur Veröffentlichung fehlt.")


@transaction.atomic
def publish_article(article_id, *, user):
    require_publisher(user)
    content_lock()
    article = Article.objects.select_for_update().get(pk=article_id)
    if not article.author_id:
        raise ValidationError("Vor der Veröffentlichung eine Autorendarstellung festlegen.")
    images = Media.objects.filter(pk=article.hero_image_id) | article.images.all()
    if any(not image.alt_text.strip() for image in images):
        raise ValidationError("Alle Artikelbilder benötigen einen Alternativtext.")
    article.status = Article.Status.PUBLISHED
    article.editor = user
    article.save()
    return article


@transaction.atomic
def withdraw_article(article_id, *, user):
    require_publisher(user)
    content_lock()
    article = Article.objects.select_for_update().get(pk=article_id)
    article.status = Article.Status.DRAFT
    article.featured = False
    article.save()
    return article


@transaction.atomic
def set_featured(article_id, *, user):
    require_publisher(user)
    content_lock()
    try:
        article = Article.objects.public().select_for_update().get(pk=article_id)
    except Article.DoesNotExist as exc:
        raise ValidationError("Nur ein aktuell sichtbarer Artikel kann Aufmacher werden.") from exc
    Article.objects.filter(featured=True).update(featured=False)
    article.featured = True
    article.save(update_fields=["featured"])
    return article
