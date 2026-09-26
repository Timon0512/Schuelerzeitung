from django.contrib import admin
from django.urls import path
from news.views import media_file, private_media, article_preview
from news import public
from news.views import site_logo
from news.sitemaps import sitemaps
from django.contrib.sitemaps.views import index, sitemap
from django.views.decorators.cache import never_cache

admin.site.site_header = "KAKTUS Redaktion"
admin.site.site_title = "KAKTUS"
admin.site.index_title = "Redaktionsverwaltung"
urlpatterns = [path("admin/", admin.site.urls), path("medien/<uuid:pk>", media_file, name="media"),
               path("redaktion/medien/<uuid:pk>", private_media, name="private_media"),
               path("redaktion/vorschau", article_preview, name="article_preview"),
               path("", public.home, name="home"),
               path("artikel", public.article_list, name="articles"),
               path("artikel/<slug:slug>", public.article_detail, name="article"),
               path("rubrik/<slug:slug>", public.category, name="category"),
               path("autoren", public.authors, name="authors"),
               path("autor/<slug:slug>", public.author_detail, name="author"),
               path("suche", public.search, name="search"),
               path("artikel-einreichen", public.submission, name="submission"),
               path("zeitungslogo", site_logo, name="site_logo"),
               path("sitemap.xml", never_cache(index), {"sitemaps": sitemaps, "sitemap_url_name": "sitemap_section"}, name="sitemap"),
               path("sitemap-<section>.xml", never_cache(sitemap), {"sitemaps": sitemaps}, name="sitemap_section"),
               ]
for page in ("mitmachen", "ueber-uns", "impressum", "datenschutz"):
    urlpatterns.append(path(page, public.information, {"page": page}, name=page))

handler404 = "news.public.error_404"
handler500 = "news.public.error_500"
