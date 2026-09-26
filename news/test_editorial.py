from io import BytesIO
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from PIL import Image
from .models import Article, Category, Author, Media
from .forms import MediaForm
from .services import publish_article, withdraw_article
from submissions.models import Submission
from submissions.services import convert_submission


class EditorialTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.category = Category.objects.create(name="Schule", slug="schule")
        self.author = Author.objects.create(display_name="Redaktion", slug="redaktion")
        self.editor = get_user_model().objects.create_user("editor", is_staff=True)
        self.editor.groups.add(Group.objects.get(name="Redaktion"))
        self.publisher = get_user_model().objects.create_user("publisher", is_staff=True)
        self.publisher.groups.add(Group.objects.get(name="Veröffentlichung"))
        self.article = Article.objects.create(title="Test", slug="test", category=self.category, author=self.author)
        self.client.force_login(self.editor)

    def data(self, **kwargs):
        return {"title": "Geändert", "slug": "test", "category": self.category.pk, "author": self.author.pk,
                "body": "<p>Entwurf</p>", "_save": "Speichern", **kwargs}

    def image(self, uploaded_by=None):
        source = BytesIO()
        Image.new("RGB", (8, 8)).save(source, "PNG")
        form = MediaForm({"alt_text": "Testbild", "caption": "Bildunterschrift"}, {"file": SimpleUploadedFile("test.png", source.getvalue())})
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save(commit=False)
        obj.uploaded_by = uploaded_by
        obj.save()
        return obj

    def test_standard_admin_cannot_publish_or_modify_live_article(self):
        url = reverse("admin:news_article_change", args=[self.article.pk])
        self.assertEqual(self.client.post(url, self.data(status="published")).status_code, 403)
        self.assertEqual(self.client.post(url, self.data()).status_code, 302)
        publish_article(self.article.pk, user=self.publisher)
        self.assertEqual(self.client.post(url, self.data()).status_code, 403)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "published")

    def test_admin_action_and_shared_metadata_protection(self):
        url = reverse("admin:news_article_changelist")
        self.assertEqual(self.client.post(url, {"action": "publish", "_selected_action": self.article.pk}).status_code, 403)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "draft")
        self.client.force_login(self.publisher)
        self.client.post(url, {"action": "publish", "_selected_action": self.article.pk})
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, "published")
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(reverse("admin:news_author_change", args=[self.author.pk]), {"display_name": "Angriff", "slug": "redaktion"}).status_code, 403)

    def test_conversion_is_idempotent_and_private_identity_not_copied(self):
        submission = Submission.objects.create(name="Privater Name", class_level="9c", title="Einsendung", category=self.category, body="<script>test</script>")
        first = convert_submission(submission.pk, user=self.editor)
        second = convert_submission(submission.pk, user=self.editor)
        self.assertEqual(first.pk, second.pk)
        self.assertIsNone(first.author_id)
        self.assertEqual(first.status, "draft")
        self.assertNotIn("Privater Name", first.body)
        self.assertNotIn("<script>", first.body)
        submission.refresh_from_db()
        self.assertEqual(submission.class_level, "9c")

    def test_private_image_cannot_be_injected_and_media_access_revokes(self):
        private = self.image()
        Submission.objects.create(name="Intern", class_level="7", title="Privat", category=self.category, body="Text", image=private)
        url = reverse("admin:news_article_change", args=[self.article.pk])
        response = self.client.post(url, self.data(hero_image=str(private.pk)))
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertIsNone(self.article.hero_image_id)
        image = self.image(self.editor)
        response = self.client.post(url, self.data(text_images=[str(image.pk)], body=f'<img data-media-id="{image.pk}" src="https://evil.test">'))
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertIn(f"/medien/{image.pk}", self.article.body)
        anonymous = Client()
        self.assertEqual(anonymous.get(reverse("private_media", args=[image.pk])).status_code, 302)
        self.assertEqual(anonymous.get(reverse("media", args=[image.pk])).status_code, 404)
        publish_article(self.article.pk, user=self.publisher)
        response = anonymous.get(reverse("media", args=[image.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        withdraw_article(self.article.pk, user=self.publisher)
        self.assertEqual(anonymous.get(reverse("media", args=[image.pk])).status_code, 404)

    def test_preview_uses_post_is_private_and_does_not_save(self):
        url = reverse("article_preview")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Client().post(url, self.data()).status_code, 302)
        response = self.client.post(url, self.data(article_id=self.article.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geändert")
        self.assertIn("noindex", response["X-Robots-Tag"])
        self.assertIn("no-store", response["Cache-Control"])
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Test")
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.editor)
        self.assertEqual(csrf.post(url, self.data()).status_code, 403)
