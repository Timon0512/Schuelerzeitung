"""Read-only public pages. Every article entry point uses the public selector."""
from datetime import timedelta
from math import ceil

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_safe

from .content import clean_body
from .models import Category, SiteSetting
from .selectors import public_articles, public_authors, resolve_article


def site_context():
    return {"site": SiteSetting.objects.select_related("logo").first() or SiteSetting(),
            "nav_categories": Category.objects.filter(is_active=True)}


def public_render(request, template, context=None, *, status=200):
    data = site_context()
    data.update(context or {})
    data.setdefault("description", "Die Schülerzeitung des " + data["site"].school_name + ".")
    page = data.get("page_obj")
    canonical_path = request.path + (f"?page={page.number}" if page and page.number > 1 else "")
    data.setdefault("canonical", request.build_absolute_uri(canonical_path))
    response = render(request, template, data, status=status)
    # Withdrawals and changes to author/media grants must take effect next request.
    response["Cache-Control"] = "private, no-store"
    if data.get("noindex"):
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def paginate(request, articles):
    return Paginator(articles, 12).get_page(request.GET.get("page"))


@require_safe
def home(request):
    articles = public_articles()
    lead = articles.lead()
    remaining = articles.exclude(pk=lead.pk) if lead else articles
    side = list(remaining[:2])
    latest = remaining.exclude(pk__in=[item.pk for item in side])[:6]
    now = timezone.now()
    popular = articles.annotate(week_hearts=Count("reactions", filter=Q(
        reactions__created_at__gte=now - timedelta(days=7),
        reactions__created_at__lte=now))).filter(week_hearts__gt=0).order_by(
            "-week_hearts", "-published_at", "-pk")[:5]
    return public_render(request, "news/home.html", {
        "lead": lead, "side_articles": side, "latest": latest, "popular": popular,
        "pause": Category.objects.filter(is_active=True, slug="pausenecke").first(),
        "rubrics": [(category, list(articles.filter(category=category)[:3]))
                    for category in Category.objects.filter(is_active=True).exclude(slug="pausenecke")],
    })


@require_safe
def article_list(request):
    return public_render(request, "news/list.html", {
        "title": "Alle Artikel", "page_obj": paginate(request, public_articles())})


@require_safe
def category(request, slug):
    rubric = get_object_or_404(Category, slug=slug, is_active=True)
    return public_render(request, "news/list.html", {
        "title": rubric.name, "category": rubric,
        "page_obj": paginate(request, public_articles().filter(category=rubric))})


def article_context(article, *, images=None, private=False):
    captions = {}
    if images is None:
        placements = list(article.image_placements.select_related("media"))
        images = [placement.media for placement in placements]
        captions = {str(placement.media_id): placement.caption for placement in placements}
    elif article.pk and not article._state.adding:
        captions = {str(p.media_id): p.caption for p in article.image_placements.all()}
    return {"article": article, "title": article.title, "description": article.excerpt or strip_tags(article.body)[:180],
            "article_body": clean_body(article.body, images, private=private, render=True, captions=captions),
            "reading_minutes": max(1, ceil(len(strip_tags(article.body).split()) / 200)),
            "is_preview": private, "noindex": private, "og_type": "article"}


@require_safe
def article_detail(request, slug):
    article, redirected = resolve_article(slug)
    if article is None:
        raise Http404
    if redirected:
        # Avoid a permanently cached redirect surviving article withdrawal.
        response = HttpResponseRedirect(reverse("article", args=[article.slug]))
        response["Cache-Control"] = "private, no-store"
        return response
    data = article_context(article)
    data["related"] = public_articles().filter(category_id=article.category_id).exclude(pk=article.pk)[:3]
    data["heart_count"] = article.reactions.count()
    from reactions.services import visitor_token, token_hash, ensure_cookie
    token = visitor_token(request)
    data.update(hearts_enabled=True, heart_action=reverse("heart", args=[article.slug]),
                heart_state="ready", heart_selected=bool(token and article.reactions.filter(visitor_token_hash=token_hash(token)).exists()))
    if article.hero_image_id:
        data["og_image"] = request.build_absolute_uri(reverse("media", args=[article.hero_image_id]))
    return ensure_cookie(request, public_render(request, "news/article.html", data))


@require_safe
def authors(request):
    return public_render(request, "news/authors.html", {
        "title": "Die Redaktion", "page_obj": paginate(request, public_authors().order_by("display_name", "pk"))})


@require_safe
def author_detail(request, slug):
    author = get_object_or_404(public_authors(), slug=slug)
    return public_render(request, "news/list.html", {
        "title": author.display_name, "author": author,
        "page_obj": paginate(request, public_articles().filter(author=author))})


@require_safe
def search(request):
    query = request.GET.get("q", "").strip()[:200]
    articles = public_articles().none()
    if query:
        articles = public_articles().filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(body_text__icontains=query)
            | Q(category__name__icontains=query)
            | Q(author__display_name__icontains=query, author__is_public=True))
    return public_render(request, "news/list.html", {
        "title": "Suche", "is_search": True, "query": query, "noindex": True,
        "page_obj": paginate(request, articles)})


@require_safe
def information(request, page):
    titles = {"mitmachen": "Mitmachen", "ueber-uns": "Über uns",
              "impressum": "Impressum", "datenschutz": "Datenschutz"}
    return public_render(request, "news/information.html", {
        "title": titles[page], "information_page": page,
        "noindex": page in ("impressum", "datenschutz")})


def error_404(request, exception):
    # No database dependency: these pages also work during an outage.
    return render(request, "news/error.html", {"site": SiteSetting(), "title": "Seite nicht gefunden",
        "error_message": "Diese Seite ist nicht verfügbar. Vielleicht wurde der Artikel zurückgezogen oder die Adresse geändert.",
        "noindex": True}, status=404)


def error_500(request):
    return render(request, "news/error.html", {"site": SiteSetting(), "title": "Gerade nicht erreichbar",
        "error_message": "Die Zeitung kann gerade nicht geladen werden. Bitte versuche es später noch einmal.",
        "noindex": True}, status=500)
