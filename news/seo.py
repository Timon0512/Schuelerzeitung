"""Metadata for public pages; use only explicitly public author information."""
import json
from html import unescape

from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


def plain_description(value, limit=180):
    # Separate block elements before stripping tags to preserve word boundaries.
    text = " ".join(unescape(strip_tags(str(value).replace("><", "> <"))).split())
    if len(text) <= limit:
        return text
    return text[:limit - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def metadata(request, data):
    site = data["site"]
    page = data.get("page_obj")
    number = page.number if page else 1
    title = data.get("title")
    if title:
        seo_title = f"{title} · {site.publication_name}"
    else:
        seo_title = f"{site.publication_name} – Schülerzeitung am {site.school_name}"
    if number > 1:
        seo_title = f"{title or site.publication_name} · Seite {number} · {site.publication_name}"

    description = data.get("description")
    if not description:
        if data.get("category"):
            description = f"{data['category'].name}: Artikel und Perspektiven aus {site.publication_name}, der Schülerzeitung am {site.school_name}."
        elif data.get("author"):
            author = data["author"]
            description = author.bio or f"Artikel von {author.display_name} in {site.publication_name}, der Schülerzeitung am {site.school_name}."
        elif request.path == reverse("articles"):
            description = f"Alle Artikel aus {site.publication_name}: Nachrichten, Meinungen und Geschichten aus der Schulgemeinschaft am {site.school_name}."
        elif request.path == reverse("authors"):
            description = f"Die Redaktion von {site.publication_name}: Lerne die Autorinnen und Autoren der Schülerzeitung am {site.school_name} kennen."
        elif data.get("information_page") == "mitmachen":
            description = f"Bei {site.publication_name} mitmachen: Erfahre, wie deine Ideen und Beiträge Teil der Schülerzeitung am {site.school_name} werden."
        elif data.get("information_page") == "ueber-uns":
            description = f"Über {site.publication_name}, die Schülerzeitung am {site.school_name}: Geschichten und Perspektiven aus unserer Schulgemeinschaft."
        else:
            description = f"{site.publication_name}, die Schülerzeitung am {site.school_name}: Nachrichten, Meinungen und Geschichten aus unserer Schulgemeinschaft."
    description = plain_description(description)
    if number > 1:
        description = f"Seite {number}: {description}"
    result = {"seo_title": seo_title, "description": description,
              "google_site_verification": settings.GOOGLE_SITE_VERIFICATION}
    if data.get("noindex"):
        return result

    home_url = request.build_absolute_uri(reverse("home"))
    publisher = {"@type": "Organization", "name": site.publication_name, "url": home_url}
    structured = None
    if request.path == reverse("home"):
        structured = {"@context": "https://schema.org", "@type": "WebSite",
                      "name": site.publication_name, "url": home_url,
                      "description": description, "inLanguage": "de-DE", "publisher": publisher}
    article = data.get("article")
    if article:
        structured = {"@context": "https://schema.org", "@type": "NewsArticle",
                      "headline": article.title, "description": description,
                      "url": data["canonical"], "mainEntityOfPage": data["canonical"],
                      "inLanguage": "de-DE", "articleSection": article.category.name,
                      "publisher": publisher}
        for field, value in (("datePublished", article.published_at), ("dateModified", article.updated_at)):
            if value:
                structured[field] = value.isoformat()
        credits = [
            {"@type": "Person", "name": author.display_name,
             "url": request.build_absolute_uri(reverse("author", args=[author.slug]))}
            for author in data.get("public_article_authors", ())
        ]
        if credits:
            structured["author"] = credits[0] if len(credits) == 1 else credits
        if data.get("og_image"):
            structured["image"] = [data["og_image"]]
    if structured:
        # JSON in an HTML script element must escape '<', including '</script>'.
        encoded = json.dumps(structured, ensure_ascii=False).translate(
            {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"})
        result["structured_data"] = mark_safe(encoded)
    return result
