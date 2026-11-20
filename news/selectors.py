from django.db.models import Prefetch

from .models import Article, Author, SlugRedirect


def public_articles():
    return Article.objects.public().select_related("category", "hero_image")


def public_articles_with_authors():
    authors = Author.objects.filter(is_public=True).order_by("display_name", "pk")
    return public_articles().prefetch_related(Prefetch("authors", queryset=authors, to_attr="public_authors"))


def public_authors():
    return Author.objects.public()


def articles_by_author(slug):
    return public_articles().filter(authors__slug=slug, authors__is_public=True)


def resolve_article(slug):
    article = public_articles().filter(slug=slug).first()
    if article:
        return article, False
    redirect = SlugRedirect.objects.filter(slug=slug, article__in=public_articles()).select_related("article").first()
    return (redirect.article, True) if redirect else (None, False)
