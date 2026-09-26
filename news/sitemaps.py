from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Category
from .selectors import public_articles, public_authors


class ArticleSitemap(Sitemap):
    limit = 1000

    def items(self):
        return public_articles()

    def location(self, item):
        return reverse("article", args=[item.slug])

    def lastmod(self, item):
        return item.updated_at


class StaticSitemap(Sitemap):
    def items(self):
        return ["home", "articles", "authors", "mitmachen", "ueber-uns"]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, item):
        return reverse("category", args=[item.slug])


class AuthorSitemap(Sitemap):
    def items(self):
        return public_authors().order_by("pk")

    def location(self, item):
        return reverse("author", args=[item.slug])


sitemaps = {"articles": ArticleSitemap, "pages": StaticSitemap, "categories": CategorySitemap, "authors": AuthorSitemap}
