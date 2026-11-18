from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from submissions.models import Submission
from .content import clean_body
from .models import Article, Author, Category, Media


class AdminWorkspaceTests(TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        media_folder = override_settings(MEDIA_ROOT=folder.name)
        media_folder.enable()
        self.addCleanup(media_folder.disable)
        self.category = Category.objects.create(name="Schule", slug="schule")
        self.author = Author.objects.create(display_name="Redaktion", slug="redaktion", is_public=True)
        self.editor = get_user_model().objects.create_user("redaktion", is_staff=True)
        self.editor.groups.add(Group.objects.get(name="Redaktion"))
        self.publisher = get_user_model().objects.create_user("freigabe", is_staff=True)
        self.publisher.groups.add(Group.objects.get(name="Veröffentlichung"))
        self.client.force_login(self.editor)

    def photo(self):
        png = BytesIO()
        Image.new("RGB", (80, 60), "orange").save(png, "PNG")
        return SimpleUploadedFile("foto.png", png.getvalue(), content_type="image/png")

    def test_upload_preview_and_publication_from_new_article(self):
        picker = reverse("admin:news_article_add_media")
        add = reverse("admin:news_article_add")
        self.assertContains(self.client.get(add), "Titelbild")
        secured = Client(enforce_csrf_checks=True)
        secured.force_login(self.editor)
        self.assertEqual(secured.post(picker, {"alt_text": "Foto", "file": self.photo()}).status_code, 403)
        failure = self.client.post(picker, {"alt_text": "", "file": self.photo()})
        self.assertEqual(failure.status_code, 400)
        self.assertIn("alt_text", failure.json()["errors"])
        self.assertFalse(Media.objects.exists())
        uploaded = self.client.post(picker, {"alt_text": "Testfoto", "caption": "Sommerfest", "file": self.photo()})
        self.assertEqual(uploaded.status_code, 201)
        photo = uploaded.json()
        self.assertEqual(self.client.get(picker, {"q": "sommerfest"}).json()["images"], [photo])
        self.assertEqual(self.client.get(photo["thumb"]).status_code, 200)
        self.assertEqual(Client().get(reverse("media", args=[photo["id"]])).status_code, 404)
        body = f'<p>Text</p><img data-media-id="{photo["id"]}" data-crop="4-3/15/75/150">'
        form = {
            "title": "Schulfest", "slug": "schulfest", "category": self.category.pk, "authors": [self.author.pk],
            "body": body, "hero_image": photo["id"], "hero_focus_image": photo["id"],
            "hero_focus_x": 25, "hero_focus_y": 70, "hero_zoom": 160,
        }
        preview = self.client.post(reverse("article_preview"), form)
        self.assertContains(preview, 'class="title-crop"')
        self.assertContains(preview, '--crop-zoom:1.6')
        self.assertContains(preview, 'data-crop="4-3/15/75/150"')
        self.assertContains(preview, photo["src"])
        self.assertFalse(Article.objects.exists())
        self.assertEqual(self.client.post(add, {**form, "_publish": "1"}).status_code, 403)
        draft = self.client.post(add, {**form, "_continue": "1"})
        article = Article.objects.get(slug="schulfest")
        change = reverse("admin:news_article_change", args=[article.pk])
        self.assertRedirects(draft, change, fetch_redirect_response=False)
        self.assertEqual(article.hero_zoom, 160)
        self.assertIn('data-crop="4-3/15/75/150"', article.body)
        self.client.force_login(self.publisher)
        invalid = self.client.post(change, {**form, "title": "Unvollständig", "authors": [], "_publish": "1"})
        self.assertContains(invalid, "mindestens eine Autorendarstellung")
        article.refresh_from_db()
        self.assertEqual((article.title, article.status), ("Schulfest", Article.Status.DRAFT))
        result = self.client.post(change, {**form, "title": "Schulfest am Freitag", "_publish": "1"})
        self.assertRedirects(result, change, fetch_redirect_response=False)
        public_url = reverse("article", args=[article.slug])
        public = Client().get(public_url)
        self.assertContains(public, "Schulfest am Freitag")
        self.assertContains(public, 'class="title-crop"')
        self.assertContains(public, 'class="text-crop"')
        self.assertNotContains(public, "/redaktion/medien/")
        self.client.force_login(self.editor)
        self.assertContains(self.client.get(change), "Schulfest am Freitag")
        self.assertNotContains(self.client.get(change), 'name="_publish"')
        self.assertEqual(self.client.get(reverse("admin:news_article_media", args=[article.pk])).status_code, 403)
        self.client.force_login(self.publisher)
        status_url = reverse("admin:news_article_status", args=[article.pk])
        self.assertEqual(self.client.post(status_url, {"editor_action": "feature"}).status_code, 302)
        self.assertContains(Client().get(reverse("home")), 'story-image title-crop')
        self.assertEqual(self.client.post(status_url, {"editor_action": "withdraw"}).status_code, 302)
        self.assertEqual(Client().get(public_url).status_code, 404)
        self.assertEqual(Client().get(reverse("media", args=[photo["id"]])).status_code, 404)

    def test_submission_detail_actions_and_attachment_scope(self):
        photo = Media(
            file=self.photo(), alt_text="Privates Foto", submission_origin=True,
        )
        photo.save()
        entry = Submission.objects.create(
            category=self.category, title="Zeitungsbeitrag", body="Der Beitrag",
            name="Interner Name", class_level="8b", image=photo,
        )
        detail = reverse("admin:submissions_submission_change", args=[entry.pk])
        self.assertContains(self.client.get(detail), "Als Entwurf übernehmen")
        self.client.post(detail, {"editor_note": "Bild prüfen", "_submission_action": "review"})
        entry.refresh_from_db()
        self.assertEqual(entry.status, Submission.Status.IN_REVIEW)
        self.assertEqual(entry.editor_note, "Bild prüfen")
        picker = reverse("admin:news_article_add_media")
        self.assertEqual(self.client.get(picker).json()["images"], [])
        response = self.client.post(detail, {"editor_note": "Geprüft", "_submission_action": "convert"})
        entry.refresh_from_db()
        article = entry.article
        self.assertRedirects(response, reverse("admin:news_article_change", args=[article.pk]), fetch_redirect_response=False)
        self.assertNotIn(entry.name, article.body)
        self.assertFalse(article.authors.exists())
        article_picker = reverse("admin:news_article_media", args=[article.pk])
        self.assertEqual(self.client.get(article_picker).json()["images"][0]["id"], str(photo.pk))
        self.assertEqual(self.client.get(picker).json()["images"], [])
        repeated = self.client.post(detail, {"editor_note": "Geprüft", "_submission_action": "convert"})
        self.assertEqual(repeated.url, response.url)
        self.assertEqual(Article.objects.count(), 1)

    def test_text_image_crop_is_per_occurrence_and_sanitized(self):
        image = Media(width=100, height=80)
        source = (
            f'<img data-media-id="{image.pk}" data-crop="1-1/80/15/140">'
            f'<img data-media-id="{image.pk}" data-crop="16-9/22/87/190">'
            f'<img data-media-id="{image.pk}" data-crop="4-3/0/100/999" style="display:none">'
        )
        saved = clean_body(source, [image])
        self.assertIn('data-crop="1-1/80/15/140"', saved)
        self.assertIn('data-crop="16-9/22/87/190"', saved)
        self.assertNotIn("999", saved)
        self.assertNotIn("display:none", saved)
        rendered = clean_body(saved, [image], render=True)
        self.assertEqual(rendered.count('class="text-crop"'), 2)
