"""Render actual Django templates without a database; synthetic QA content only."""
import os
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "local-check-only-not-for-serving")
import django
django.setup()
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory
from news.models import Article, Author, Category, Media, SiteSetting
from news.public import article_context
from news.submission_ui import SubmissionUIForm


def fixtures():
    categories = [Category(pk=i+1, name=name, slug=slug) for i, (name, slug) in enumerate([
        ("Schule", "schule"), ("Meinung", "meinung"), ("Kultur", "kultur"), ("Sport", "sport"), ("Pausenecke", "pausenecke")])]
    author = Author(pk=1, display_name="Beispielredaktion", slug="beispiel", is_public=True,
                    bio="Fiktive Autorendarstellung für die Layoutprüfung.")
    media = Media(alt_text="Beschriftete Testfläche, kein Schulfoto", caption="Testgrafik für die Layoutprüfung – kein Nachrichtenfoto.", width=2400, height=1200, small_file="fixture-small.webp", small_width=640, small_height=320, large_file="fixture-large.webp", large_width=1920, large_height=960)
    titles = ["Eine Woche voller neuer Ideen", "Mehr Raum für unsere Perspektiven", "Was wir gerade lesen", "Gemeinsam etwas bewegen", "Ein Blick hinter die Kulissen", "Geschichten aus dem Schulalltag"]
    articles = [Article(pk=i+1, title=title, slug=f"beispiel-{i}", category=categories[i % 4], author=author,
        hero_image=media, status="published", published_at=datetime(2026,9,25-i,tzinfo=timezone.utc),
        excerpt="Fiktiver Beispieltext: Neue Ideen, gemeinsame Projekte und ein anderer Blick auf den Alltag.",
        body=f'<p>Dies ist ein fiktiver Beitrag zur Layoutprüfung. Er beschreibt keine tatsächliche Schulnachricht.</p><h2>Von der Idee zum gemeinsamen Projekt</h2><p>Ein guter Artikel macht neugierig, erklärt Zusammenhänge und lässt unterschiedliche Perspektiven zu Wort kommen.</p><p><img data-media-id="{media.pk}"></p><h2>Was wir mitnehmen</h2><p>Hier bleibt Platz für die Geschichten der Schulgemeinschaft. Die Redaktion prüft alle Texte vor der Veröffentlichung.</p>',
        body_text="Beispieltext " * 210) for i, title in enumerate(titles)]
    base = {"site": SiteSetting(), "nav_categories": categories, "description": "Isolierte Layoutprüfung mit fiktiven Inhalten.",
            "noindex": True}
    def render(template, **data):
        return render_to_string(template, {**base, **data}, request=RequestFactory().get("/"))
    pages = {"home": render("news/home.html", lead=articles[0], side_articles=articles[1:3], latest=articles[3:],
                            popular=[], pause=categories[-1], rubrics=[]),
             "empty-home": render("news/home.html"),
             "article": render("news/article.html", **article_context(articles[0], images=[media]), related=[articles[4]]),
             "list": render("news/list.html", title="Alle Artikel", page_obj=Paginator(articles * 3, 12).page(1)),
             "empty-category": render("news/list.html", title="Schule", category=categories[0], page_obj=Paginator([],12).page(1)),
             "search": render("news/list.html", title="Suche", is_search=True, query="Kein Treffer", page_obj=Paginator([],12).page(1)),
             "authors": render("news/authors.html", title="Die Redaktion", page_obj=Paginator([author],12).page(1)),
             "author": render("news/list.html", title=author.display_name, author=author, page_obj=Paginator(articles,12).page(1)),
             "404": render("news/error.html", title="Seite nicht gefunden", error_message="Diese Seite ist nicht verfügbar."),
             "500": render("news/error.html", title="Gerade nicht erreichbar", error_message="Bitte versuche es später noch einmal.")}
    preview_article = Article(title=articles[0].title, slug="preview", category=categories[0], author=author, hero_image=media,
                              body=articles[0].body, body_text=articles[0].body_text)
    pages["preview"] = render("news/article.html", **article_context(preview_article, images=[media], private=True))
    long = Article(title="Ein sehr langer Titel über Schülerzeitungsredaktionskonferenzvorbereitungen " * 4,
                   slug="long", category=categories[0], author=author, body="<p>Lesetext ohne Titelbild.</p>")
    pages["long-title"] = render("news/article.html", **article_context(long, images=[]))
    for state in ["disabled", "error", "pending", "received"]:
        form = SubmissionUIForm({"name":"Erhaltene Eingabe", "title":"Mein Beitrag"} if state == "error" else None)
        form.fields["category"].queryset = Category.objects.none()
        pages["submission-"+state] = render("news/submission.html", title="Artikel einreichen", form=form,
            submission_enabled=state != "disabled", submission_state=state, submission_received=state == "received")
    for state in ["unset", "selected", "pending", "error"]:
        pages["heart-"+state] = render("news/article.html", **article_context(articles[0], images=[media]),
            hearts_enabled=True, heart_state=state, heart_selected=state in ("selected", "error"), heart_action="/fixture-only", heart_count=3)
    for page in ["mitmachen", "ueber-uns", "impressum", "datenschutz"]:
        pages[page] = render("news/information.html", title=page.replace("-", " ").capitalize(), information_page=page)
    return pages, media


if __name__ == "__main__":
    output = Path(".qa/frontend")
    output.mkdir(parents=True, exist_ok=True)
    pages, media = fixtures()
    for name, html in pages.items():
        (output / f"{name}.html").write_text(html, encoding="utf-8")
    (output / "image-id.txt").write_text(str(media.pk), encoding="utf-8")
    print(f"Rendered {len(pages)} real-template fixtures, without database access.")
