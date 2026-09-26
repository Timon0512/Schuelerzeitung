import unittest
from unittest.mock import patch
from tests.frontend_fixtures import fixtures
from django.test import RequestFactory, SimpleTestCase
from news import public
from news.content import clean_body
from news.models import SiteSetting


class FrontendUnitTests(SimpleTestCase):
    def test_templates_and_unavailable_interactions(self):
        pages, _ = fixtures()
        self.assertEqual(len(pages), 24)
        self.assertIn('<fieldset disabled', pages['submission-disabled'])
        self.assertIn('keine Daten versendet', pages['submission-disabled'])
        self.assertIn('Erhaltene Eingabe', pages['submission-error'])
        self.assertIn('error-summary', pages['submission-error'])
        self.assertIn('aria-busy="true"', pages['submission-pending'])
        self.assertIn('Dein Beitrag ist angekommen', pages['submission-received'])
        self.assertIn('aria-pressed="true"', pages['heart-selected'])
        self.assertIn('bisherige Stand bleibt erhalten', pages['heart-error'])
        self.assertIn('noindex,nofollow', pages['preview'])
        self.assertIn('/redaktion/medien/', pages['preview'])
        self.assertNotIn('src="/medien/', pages['preview'])

    def test_render_refreshes_metadata_and_escapes_captions(self):
        _, image = fixtures()
        rendered = clean_body(f'<p><img data-media-id="{image.pk}" alt="stale"></p>', [image], render=True,
                              captions={str(image.pk): '<script>caption</script>'})
        self.assertIn(image.alt_text, rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertNotIn('<figure>', rendered)
        self.assertIn('width="1200"', rendered)
        self.assertNotIn('stale', rendered)

    def test_error_pages_need_no_database(self):
        request = RequestFactory().get('/missing')
        self.assertEqual(public.error_404(request, Exception()).status_code, 404)
        self.assertEqual(public.error_500(request).status_code, 500)

    def test_submission_limits_and_honeypot(self):
        from news.submission_ui import SubmissionUIForm
        form = SubmissionUIForm()
        self.assertEqual(form.fields['title'].max_length, 200)
        self.assertTrue(form.fields['website'].widget.is_hidden)

    def test_public_render_cache_and_canonical(self):
        from django.core.paginator import Paginator
        from news.models import Article, Category
        request = RequestFactory().get('/artikel?page=2', HTTP_HOST='localhost')
        with patch('news.public.site_context', return_value={'site': SiteSetting(), 'nav_categories': []}):
            article = Article(title='Test', slug='test', category=Category(name='Test', slug='test'))
            response = public.public_render(request, 'news/list.html', {'page_obj': Paginator([article] * 13,12).page(2)})
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('http://localhost/artikel?page=2', response.content.decode())
