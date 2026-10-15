"""Verify rendered SEO output and privacy boundaries without database access."""
import json
import re
from datetime import datetime, timezone
from unittest.mock import patch

from tests.frontend_fixtures import fixtures
from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from news.models import Article, Author, Category, SiteSetting
from news.public import public_render
from news.seo import plain_description


@override_settings(ALLOWED_HOSTS=["zeitung.example.invalid"], SECURE_SSL_REDIRECT=False)
class SEOTests(SimpleTestCase):
    def render_page(self, path="/", **context):
        request = RequestFactory().get(path, secure=True, HTTP_HOST="zeitung.example.invalid")
        with patch("news.public.site_context", return_value={
                "site": SiteSetting(publication_name="Unsere Zeitung"), "nav_categories": []}):
            return public_render(request, "news/base.html", context)

    def structured(self, html):
        return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1])

    def article(self):
        return Article(
            title='Titel "mit Zitaten" </script><script>alert(1)</script>', slug="beispiel",
            category=Category(name="Schule", slug="schule"),
            author=Author(pk=1, display_name="Privater Name", slug="privat", is_public=False),
            published_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 10, 2, tzinfo=timezone.utc))

    def test_home_has_own_site_name_and_subdomain_url(self):
        html = self.render_page().content.decode()
        self.assertIn("Unsere Zeitung – Schülerzeitung am Aggertal-Gymnasium", html)
        structured = self.structured(html)
        self.assertEqual(structured["@type"], "WebSite")
        self.assertEqual(structured["name"], "Unsere Zeitung")
        self.assertEqual(structured["url"], "https://zeitung.example.invalid/")
        self.assertIn('max-image-preview:large', html)

    def test_article_json_is_valid_safe_and_hides_private_author(self):
        article = self.article()
        html = self.render_page("/artikel/beispiel?utm_source=test", article=article,
                                title=article.title, og_type="article", description="Ein Teaser.",
                                og_image="https://zeitung.example.invalid/medien/test").content.decode()
        data = self.structured(html)
        self.assertEqual(data["@type"], "NewsArticle")
        self.assertEqual(data["headline"], article.title)
        self.assertEqual(data["datePublished"], article.published_at.isoformat())
        self.assertEqual(data["dateModified"], article.updated_at.isoformat())
        self.assertEqual(data["url"], "https://zeitung.example.invalid/artikel/beispiel")
        self.assertEqual(data["image"], ["https://zeitung.example.invalid/medien/test"])
        self.assertNotIn("author", data)
        self.assertNotIn("Privater Name", html)
        self.assertNotIn("</script><script>alert", html)
        self.assertNotIn("utm_source", html)

    def test_only_approved_author_is_named(self):
        article = self.article()
        article.author.is_public = True
        data = self.structured(self.render_page("/artikel/beispiel", article=article).content.decode())
        self.assertEqual(data["author"]["name"], article.author.display_name)
        self.assertEqual(data["author"]["url"], "https://zeitung.example.invalid/autor/privat")

    def test_preview_and_search_have_no_structured_or_social_metadata(self):
        for path in ("/redaktion/vorschau", "/suche?q=test"):
            response = self.render_page(path, article=self.article(), noindex=True)
            html = response.content.decode()
            self.assertIn('content="noindex,nofollow"', html)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
            self.assertNotIn("application/ld+json", html)
            self.assertNotIn('rel="canonical"', html)
            self.assertNotIn('property="og:', html)

    def test_paginated_pages_keep_their_own_canonical_and_title(self):
        response = self.render_page("/artikel?page=2&utm_source=test", title="Alle Artikel",
                                    page_obj=Paginator(list(range(13)), 12).page(2))
        html = response.content.decode()
        self.assertIn('<title>Alle Artikel · Seite 2 · Unsere Zeitung</title>', html)
        self.assertIn('href="https://zeitung.example.invalid/artikel?page=2"', html)
        self.assertIn('content="Seite 2:', html)
        self.assertNotIn("utm_source", html)
        self.assertIn("no-store", response["Cache-Control"])
        first = self.render_page("/artikel?page=1", page_obj=Paginator([1], 12).page(1)).content.decode()
        self.assertIn('href="https://zeitung.example.invalid/artikel"', first)

    def test_descriptions_are_specific_to_each_surface(self):
        for path, context, expected in (
            ("/artikel", {}, "Alle Artikel aus Unsere Zeitung"),
            ("/autoren", {}, "Die Redaktion von Unsere Zeitung"),
            ("/rubrik/schule", {"category": Category(name="Schule")}, "Schule: Artikel"),
            ("/autor/anna", {"author": Author(display_name="Anna", bio="Annas Texte.")}, "Annas Texte."),
            ("/mitmachen", {"information_page": "mitmachen"}, "Bei Unsere Zeitung mitmachen"),
            ("/ueber-uns", {"information_page": "ueber-uns"}, "Über Unsere Zeitung"),
        ):
            with self.subTest(path=path):
                self.assertIn(expected, self.render_page(path, **context).content.decode())

    def test_description_normalizes_html_entities_and_length(self):
        self.assertEqual(plain_description("<p>Erster &amp; zweiter</p><p>Absatz.</p>"), "Erster & zweiter Absatz.")
        text = plain_description("Ein langer Text. " * 40)
        self.assertLessEqual(len(text), 180)
        self.assertTrue(text.endswith("…"))

    @override_settings(GOOGLE_SITE_VERIFICATION='token"<test>')
    def test_search_console_verification_is_escaped(self):
        html = self.render_page().content.decode()
        self.assertIn('name="google-site-verification" content="token&quot;&lt;test&gt;"', html)

    @override_settings(GOOGLE_SITE_VERIFICATION="")
    def test_verification_is_optional(self):
        self.assertNotIn("google-site-verification", self.render_page().content.decode())

    def test_robots_is_public_and_points_to_this_hosts_sitemap(self):
        response = self.client.get("/robots.txt", secure=True, HTTP_HOST="zeitung.example.invalid")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        text = response.content.decode()
        self.assertIn("Sitemap: https://zeitung.example.invalid/sitemap.xml", text)
        self.assertIn("Disallow: /admin/", text)
        self.assertNotIn("Disallow: /\n", text)
        self.assertNotIn("Disallow: /suche", text)
        self.assertEqual(resolve("/robots.txt").url_name, "robots")
