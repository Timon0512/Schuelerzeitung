"""Integration coverage; only run via the guarded PostgreSQL test runner."""
from datetime import timedelta
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.urls import reverse
from .models import Article, Author, Category, Media, SiteSetting, ArticleMedia
from reactions.models import Reaction
from submissions.models import Submission


class PublicPageTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Schule", slug="schule")
        self.author = Author.objects.create(display_name="Öffentlicher Name", slug="autor", is_public=True)
        self.visible = Article.objects.create(title="Sichtbarer Beitrag", slug="sichtbar", category=self.category,
            author=self.author, status="published", body="<p>Öffentlicher Text</p>")
        for slug, status, date in [("geheim", "draft", None), ("archiv", "archived", None),
                                    ("zukunft", "published", timezone.now()+timedelta(days=1))]:
            Article.objects.create(title="VERBORGEN-"+slug, slug=slug, category=self.category,
                                   author=self.author, status=status, published_at=date)

    def test_visibility_across_all_public_surfaces(self):
        for url in ["/", "/artikel", "/rubrik/schule", "/autor/autor", "/suche?q=Beitrag", "/sitemap-articles.xml"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "VERBORGEN")
                for slug in ("geheim", "archiv", "zukunft"):
                    self.assertNotContains(response, "/artikel/"+slug)
        for slug in ("geheim", "archiv", "zukunft"):
            self.assertEqual(self.client.get("/artikel/"+slug).status_code, 404)
        self.assertContains(self.client.get('/sitemap.xml'), 'sitemap-articles.xml')
        self.assertNotContains(self.client.get('/sitemap-pages.xml'), '/artikel-einreichen')

    def test_hidden_authors_are_not_exposed_or_searchable(self):
        self.author.is_public = False
        self.author.save()
        for url in ["/", "/artikel", "/artikel/sichtbar", "/autoren", "/sitemap-authors.xml"]:
            self.assertNotContains(self.client.get(url), self.author.display_name)
        self.assertEqual(self.client.get('/autor/autor').status_code, 404)
        self.assertContains(self.client.get('/suche', {'q': self.author.display_name}), '0 Treffer')

    def test_redirect_and_withdrawal_revoke_access(self):
        self.visible.slug = "neu"
        self.visible.save()
        response = self.client.get('/artikel/sichtbar')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/artikel/neu')
        self.assertIn('no-store', response['Cache-Control'])
        self.visible.status = 'draft'
        self.visible.save()
        for url in ['/artikel/sichtbar', '/artikel/neu', '/autor/autor']:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get('/sitemap-articles.xml'), '/artikel/neu')

    def test_search_pagination_and_related_category(self):
        for index in range(13):
            Article.objects.create(title=f'Thema {index}', slug=f'thema-{index}', category=self.category,
                                   author=self.author, status='published')
        other = Category.objects.create(name='Andere Rubrik', slug='andere')
        Article.objects.create(title='Fremder Beitrag', slug='fremd', category=other, status='published')
        response = self.client.get('/suche', {'q':'Thema', 'page':2})
        self.assertContains(response, '13 Treffer')
        self.assertContains(response, 'q=Thema&amp;page=1')
        self.assertContains(response, 'noindex,nofollow')
        self.assertNotContains(self.client.get('/artikel/sichtbar'), 'Fremder Beitrag')
        empty = Category.objects.create(name='Leer', slug='leer')
        self.assertContains(self.client.get('/rubrik/'+empty.slug), 'noch keine Artikel')
        self.assertContains(self.client.get('/suche?q=unauffindbar'), 'Keine passenden Artikel')

    def test_weekly_ranking_counts_only_recent_existing_hearts(self):
        second = Article.objects.create(title='Zweiter Beitrag', slug='zweiter', category=self.category, status='published')
        Reaction.objects.create(article=self.visible, visitor_token_hash='a'*64)
        Reaction.objects.create(article=self.visible, visitor_token_hash='b'*64)
        old = Reaction.objects.create(article=second, visitor_token_hash='c'*64)
        Reaction.objects.filter(pk=old.pk).update(created_at=timezone.now()-timedelta(days=8))
        Reaction.objects.create(article=Article.objects.get(slug='geheim'), visitor_token_hash='d'*64)
        response = self.client.get('/')
        ranked = list(response.context['popular'])
        self.assertEqual([article.pk for article in ranked], [self.visible.pk])
        self.assertEqual(ranked[0].week_hearts, 2)

    def test_rendered_media_captions_and_logo_boundary(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            media = Media.objects.create(file=ContentFile(b'test', name='logo.webp'), alt_text='Aktueller Alttext',
                caption='Neue Bildunterschrift', mime_type='image/webp', width=10, height=10, size=4)
            self.visible._allowed_images = [media]
            self.visible.body = f'<p><img data-media-id="{media.pk}"></p>'
            self.visible.save()
            ArticleMedia.objects.create(article=self.visible, media=media, caption='Bildunterschrift am Artikel')
            response = self.client.get('/artikel/sichtbar')
            self.assertContains(response, 'Aktueller Alttext')
            self.assertContains(response, 'Bildunterschrift am Artikel')
            setting = SiteSetting.objects.create(logo=media)
            response = self.client.get('/zeitungslogo')
            self.assertEqual(response.status_code, 200)
            self.assertIn('no-store', response['Cache-Control'])
            response.close()
            Submission.objects.create(name='Privat', class_level='7', title='Privat', category=self.category, body='Text', image=media)
            self.assertEqual(self.client.get('/zeitungslogo').status_code, 404)
            setting.logo = None
            setting.save()
            self.assertEqual(self.client.get('/zeitungslogo').status_code, 404)

    def test_submission_validates_before_writing(self):
        self.assertNotContains(self.client.get('/artikel-einreichen'), '<fieldset disabled')
        self.assertEqual(self.client.post('/artikel-einreichen', {'name':'Privat'}).status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
