from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from tempfile import TemporaryDirectory
from threading import Barrier
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from .models import Article, ArticleMedia, Author, Category, Media, SiteSetting, SlugRedirect
from .selectors import articles_by_author, resolve_article
from .services import publish_article, set_featured, withdraw_article
from reactions.models import Reaction
from submissions.models import Submission


class ContentTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.author = Author.objects.create(display_name="Test", slug="test", is_public=True)
        self.editor = get_user_model().objects.create_user("editor")
        self.editor.groups.add(Group.objects.get(name="Redaktion"))
        self.publisher = get_user_model().objects.create_user("publisher")
        self.publisher.groups.add(Group.objects.get(name="Veröffentlichung"))

    def article(self, slug="test", **kwargs):
        return Article.objects.create(title=slug, slug=slug, category=self.category, author=self.author, **kwargs)

    def image(self):
        return Media.objects.create(file="images/test.png", alt_text="Test", width=1, height=1, size=1, mime_type="image/png")

    def test_visibility_and_author_pages(self):
        self.article("draft")
        self.article("archived", status="archived")
        self.article("future", status="published", published_at=timezone.now() + timedelta(days=1))
        self.assertFalse(Article.objects.public().exists())
        self.assertFalse(Author.objects.public().exists())
        visible = self.article("visible", status="published")
        self.assertEqual(list(Article.objects.public()), [visible])
        self.assertEqual(list(Author.objects.public()), [self.author])
        self.author.is_public = False
        self.author.save()
        self.assertFalse(articles_by_author("test").exists())

    def test_publication_date_and_permissions(self):
        article = self.article()
        self.assertFalse(self.editor.has_perm("news.can_publish_article"))
        self.assertFalse(self.editor.has_perm("auth.change_group"))
        for operation in (publish_article, set_featured, withdraw_article):
            with self.assertRaises(PermissionDenied):
                operation(article.pk, user=self.editor)
        article = publish_article(article.pk, user=self.publisher)
        first_date = article.published_at
        withdraw_article(article.pk, user=self.publisher)
        self.assertFalse(Article.objects.public().exists())
        article = publish_article(article.pk, user=self.publisher)
        self.assertEqual(article.published_at, first_date)

    def test_lead_switch_fallback_and_constraints(self):
        first = self.article("first", status="published")
        second = self.article("second", status="published")
        self.assertEqual(Article.objects.lead(), second)
        set_featured(first.pk, user=self.publisher)
        self.assertEqual(Article.objects.lead(), first)
        set_featured(second.pk, user=self.publisher)
        self.assertEqual(Article.objects.filter(featured=True).count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Article.objects.filter(pk=first.pk).update(featured=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Article.objects.filter(pk=second.pk).update(status="draft")
        withdraw_article(second.pk, user=self.publisher)
        self.assertEqual(Article.objects.lead(), first)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Article.objects.filter(pk=first.pk).update(published_at=None)

    def test_media_visibility_shared_and_submission_private(self):
        image = self.image()
        article = self.article(hero_image=image)
        Submission.objects.create(name="Privat", class_level="7", title="Privat", category=self.category, body="Privat", image=image)
        self.assertFalse(Media.objects.public().exists())
        self.assertEqual(self.client.get(f"/medien/{image.pk}").status_code, 404)
        publish_article(article.pk, user=self.publisher)
        self.assertTrue(Media.objects.public().filter(pk=image.pk).exists())
        other = self.article("other", status="published")
        ArticleMedia.objects.create(article=other, media=image)
        withdraw_article(article.pk, user=self.publisher)
        self.assertTrue(Media.objects.public().filter(pk=image.pk).exists())
        withdraw_article(other.pk, user=self.publisher)
        self.assertFalse(Media.objects.public().exists())
        self.assertEqual(self.client.get(f"/protected-files/{image.file.name}").status_code, 404)

    def test_redirects_stay_private_and_names_reserved(self):
        article = self.article(status="published")
        article.slug = "new"
        article.save()
        article.slug = "newer"
        article.save()
        self.assertEqual(resolve_article("test"), (article, True))
        self.assertEqual(resolve_article("new"), (article, True))
        with self.assertRaises(ValidationError):
            self.article("test")
        withdraw_article(article.pk, user=self.publisher)
        self.assertEqual(resolve_article("test"), (None, False))
        article.refresh_from_db()
        article.slug = "test"
        article.save()
        self.assertFalse(SlugRedirect.objects.filter(slug="test").exists())

    def test_html_sanitized(self):
        article = self.article(body='<p onclick="bad()">Text</p><script>bad()</script><a href="javascript:bad()">Link</a><img src="/private">')
        self.assertNotIn("script", article.body)
        self.assertNotIn("onclick", article.body)
        self.assertNotIn("<img", article.body)
        self.assertIn("Text", article.body_text)

    def test_other_constraints(self):
        article = self.article()
        Reaction.objects.create(article=article, visitor_token_hash="a" * 64)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reaction.objects.create(article=article, visitor_token_hash="a" * 64)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SiteSetting.objects.create(pk=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Submission.objects.create(name="Test", class_level="7", title="Test", body="Test", category=self.category, status="converted")

    def test_demo_is_repeatable_and_media_access_revocable(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            call_command("load_demo", stdout=StringIO())
            counts = (Article.objects.count(), Media.objects.count(), Submission.objects.count())
            call_command("load_demo", stdout=StringIO())
            self.assertEqual(counts, (Article.objects.count(), Media.objects.count(), Submission.objects.count()))
            article = Article.objects.get(slug="demo-artikel")
            response = self.client.get(f"/medien/{article.hero_image_id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "private, no-store")
            response.close()
            withdraw_article(article.pk, user=self.publisher)
            self.assertEqual(self.client.get(f"/medien/{article.hero_image_id}").status_code, 404)


class ConcurrentLeadTests(TransactionTestCase):
    def test_concurrent_switches_have_one_winner(self):
        user = get_user_model().objects.create_superuser("publisher", password="test-only")
        category = Category.objects.create(name="Test", slug="test")
        articles = [Article.objects.create(title=str(i), slug=str(i), category=category, status="published") for i in range(2)]
        barrier = Barrier(2)

        def switch(pk):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                set_featured(pk, user=actor)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(switch, [article.pk for article in articles]))
        self.assertEqual(Article.objects.filter(featured=True).count(), 1)
