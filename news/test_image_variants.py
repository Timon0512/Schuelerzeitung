"""Run only with the guarded PostgreSQL test runner."""
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from news.models import Media, Article, Author, Category
from news.forms import ArticleForm
from news.image_variants import stored_files
from tests.test_image_variants_unit import upload


class ImageWorkflowTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.root = Path(directory.name)
        self.user = get_user_model().objects.create_user("images-editor", is_staff=True)
        self.user.groups.add(Group.objects.get(name="Veröffentlichung"))
        self.category = Category.objects.create(name="Schule", slug="schule")
        self.author = Author.objects.create(display_name="Redaktion", slug="redaktion")

    def image(self):
        return Media.objects.create(file=upload((800, 600)), alt_text="Foto", uploaded_by=self.user)

    def article(self, image):
        return Article.objects.create(title="Artikel", slug="artikel", category=self.category, author=self.author, hero_image=image)

    def test_variants_follow_visibility_and_private_permissions(self):
        image = self.image()
        article = self.article(image)
        public = reverse("media_variant", args=[image.pk, "small"])
        private = reverse("private_media_variant", args=[image.pk, "large"])
        self.assertEqual(self.client.get(public).status_code, 404)
        self.assertEqual(self.client.get(private).status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(private)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        response.close()
        article.status = "published"
        article.save()
        response = self.client.get(public)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        response.close()
        article.status = "draft"
        article.save()
        self.assertEqual(self.client.get(public).status_code, 404)
        image.submission_origin = True
        image.save()
        self.user.groups.clear()
        self.user.groups.add(Group.objects.get(name="Redaktion"))
        # Explicitly remove submission access while retaining media view access.
        from django.contrib.auth.models import Permission
        self.user.groups.clear()
        self.user.user_permissions.add(Permission.objects.get(codename="view_media", content_type__app_label="news"))
        self.assertEqual(self.client.get(private).status_code, 403)

    def test_replacement_and_deletion_remove_all_previous_files(self):
        image = self.image()
        old = stored_files(image)
        image.file = upload((320, 200))
        with self.captureOnCommitCallbacks(execute=True):
            image.save()
        for storage, name in old:
            self.assertFalse(storage.exists(name))
        self.assertEqual(image.small_file.name, image.large_file.name)
        current = stored_files(image)
        with self.captureOnCommitCallbacks(execute=True):
            Media.objects.filter(pk=image.pk).delete()
        for storage, name in current:
            self.assertFalse(storage.exists(name))

    def test_backfill_dry_run_idempotency_and_failure(self):
        image = Media(width=800, height=600, size=1, mime_type="image/png")
        image.file.save("legacy.png", upload((800, 600)), save=False)
        image.size = image.file.size
        image.save()
        original = image.file.name
        call_command("optimize_images", stdout=StringIO())
        image.refresh_from_db()
        self.assertFalse(image.small_file)
        with patch("news.image_variants.models.Model.save", side_effect=RuntimeError("DB write failed")):
            with self.assertRaises(CommandError):
                call_command("optimize_images", execute=True, stdout=StringIO(), stderr=StringIO())
        self.assertEqual(len(list(self.root.rglob("*.webp"))), 0)
        call_command("optimize_images", execute=True, stdout=StringIO())
        image.refresh_from_db()
        self.assertEqual(image.file.name, original)
        first = image.large_file.name
        call_command("optimize_images", execute=True, stdout=StringIO())
        image.refresh_from_db()
        self.assertEqual(image.large_file.name, first)

    def test_focus_form_and_unsaved_preview(self):
        image = self.image()
        article = self.article(image)
        data = {"title": article.title, "slug": article.slug, "category": self.category.pk,
                "author": self.author.pk, "hero_image": image.pk, "hero_focus_image": str(image.pk),
                "hero_focus_x": 20, "hero_focus_y": 80, "body": "<p>Text</p>"}
        form = ArticleForm(data, instance=article, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        article.refresh_from_db()
        self.assertEqual((article.hero_focus_x, article.hero_focus_y), (20, 80))
        self.client.force_login(self.user)
        data.update(article_id=article.pk, hero_focus_x=10)
        response = self.client.post(reverse("article_preview"), data)
        self.assertContains(response, "object-position:10% 80%")
        self.assertContains(response, f"/redaktion/medien/{image.pk}/large")
        article.refresh_from_db()
        self.assertEqual(article.hero_focus_x, 20)
        data["hero_image"] = self.image().pk
        form = ArticleForm(data, instance=article, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["hero_focus_x"], 50)
        self.assertEqual(form.cleaned_data["hero_focus_y"], 50)
