from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe
from .models import Media
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from .models import Article
from .forms import ArticleForm
from .services import require_editor
from .public import public_render, article_context
from .models import SiteSetting


def private_headers(response):
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@staff_member_required
@require_safe
def private_media(request, pk):
    if not request.user.has_perm("news.view_media"):
        raise PermissionDenied
    media = get_object_or_404(Media, pk=pk)
    if media.submission_set.exists() and not request.user.has_perm("submissions.view_submission"):
        raise PermissionDenied
    return private_headers(FileResponse(media.file.open("rb"), content_type=media.mime_type))


@staff_member_required
@require_POST
def article_preview(request):
    require_editor(request.user)
    article_id = request.POST.get("article_id")
    if article_id and (not article_id.isdecimal() or len(article_id) > 18):
        raise Http404
    article = get_object_or_404(Article, pk=article_id) if article_id else Article()
    form = ArticleForm(request.POST, instance=article, user=request.user)
    if not form.is_valid():
        return private_headers(public_render(request, "news/preview.html", {"errors": form.errors, "noindex": True, "title": "Vorschau prüfen"}, status=400))
    article = form.save(commit=False)
    data = article_context(article, images=form.cleaned_data["text_images"], private=True)
    return private_headers(public_render(request, "news/article.html", data))


@require_safe
def site_logo(request):
    setting = get_object_or_404(SiteSetting.objects.select_related("logo"), pk=1, logo__isnull=False, logo__submission__isnull=True)
    try:
        response = FileResponse(setting.logo.file.open("rb"), content_type=setting.logo.mime_type)
    except FileNotFoundError:
        raise Http404
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_safe
def media_file(request, pk):
    media = get_object_or_404(Media.objects.public(), pk=pk)
    response = FileResponse(media.file.open("rb"), content_type=media.mime_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
