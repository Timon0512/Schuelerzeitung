from io import BytesIO
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from PIL import Image
from .models import Article, Category, Author, EditorialProfile, Media
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
        self.article = Article.objects.create(title="Test", slug="test", category=self.category)
        self.article.authors.add(self.author)
        self.client.force_login(self.editor)

    def data(self, **kwargs):
        return {"title": "Geändert", "slug": "test", "category": self.category.pk, "authors": [self.author.pk],
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

    def test_admin_saves_multiple_authors_and_previews_unsaved_selection(self):
        self.author.is_public = True
        self.author.save()
        second = Author.objects.create(display_name="Zweite Person", slug="zweite", is_public=True)
        url = reverse("admin:news_article_change", args=[self.article.pk])
        self.assertContains(self.client.get(url), 'name="authors"', count=2)
        data = self.data(authors=[self.author.pk, second.pk])
        preview = self.client.post(reverse("article_preview"), {**data, "article_id": self.article.pk})
        self.assertContains(preview, "Redaktion und Zweite Person")
        self.assertEqual(list(self.article.authors.all()), [self.author])
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertCountEqual(self.article.authors.all(), [self.author, second])

        publish_article(self.article.pk, user=self.publisher)
        self.client.force_login(self.publisher)
        self.assertContains(self.client.post(url, self.data(authors=[])), "mindestens eine Autorendarstellung")
        self.assertCountEqual(self.article.authors.all(), [self.author, second])

        withdraw_article(self.article.pk, user=self.publisher)
        self.assertEqual(self.client.post(url, self.data(authors=[])).status_code, 302)
        self.assertFalse(self.article.authors.exists())
        with self.assertRaisesMessage(ValidationError, "mindestens eine Autorendarstellung"):
            publish_article(self.article.pk, user=self.publisher)

    def test_editorial_profile_publisher_controls_public_photo_and_text(self):
        photo = self.image(self.editor)
        private = self.image()
        Submission.objects.create(
            name="Intern", class_level="7", title="Privat", category=self.category, body="Text", image=private
        )
        add_url = reverse("admin:news_editorialprofile_add")
        photo_url = reverse("media", args=[photo.pk])
        anonymous = Client()
        self.assertEqual(anonymous.get(photo_url).status_code, 404)
        data = {"intro": "Wir stellen unser Team vor.\n\nDie zweite Zeile.", "photo": photo.pk}
        self.assertEqual(self.client.post(add_url, data).status_code, 403)
        self.client.force_login(self.publisher)
        self.assertContains(self.client.post(add_url, {**data, "photo": private.pk}), "gültige Auswahl")
        self.assertFalse(EditorialProfile.objects.exists())

        self.assertEqual(self.client.post(add_url, data).status_code, 302)
        self.assertEqual(self.client.get(add_url).status_code, 403)
        public_page = anonymous.get(reverse("authors"))
        self.assertContains(public_page, "<p>Wir stellen unser Team vor.</p>", html=True)
        self.assertContains(public_page, "<p>Die zweite Zeile.</p>", html=True)
        self.assertContains(public_page, photo_url)
        self.assertContains(public_page, 'alt="Testbild"')
        self.assertNotContains(public_page, "Die Redaktion stellt sich bald vor.")
        photo_response = anonymous.get(photo_url)
        self.assertEqual(photo_response.status_code, 200)
        self.assertTrue(b"".join(photo_response.streaming_content))

        change_url = reverse("admin:news_editorialprofile_change", args=[1])
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(change_url, {"intro": "", "photo": ""}).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:news_media_change", args=[photo.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("admin:news_media_change", args=[photo.pk])).status_code, 403)
        self.client.force_login(self.publisher)
        self.assertEqual(self.client.post(change_url, {"intro": data["intro"], "photo": ""}).status_code, 302)
        self.assertEqual(anonymous.get(photo_url).status_code, 404)
        self.assertContains(anonymous.get(reverse("authors")), "Wir stellen unser Team vor.")

    def test_conversion_is_idempotent_and_private_identity_not_copied(self):
        submission = Submission.objects.create(name="Privater Name", class_level="9c", title="Einsendung", category=self.category, body="<script>test</script>")
        first = convert_submission(submission.pk, user=self.editor)
        second = convert_submission(submission.pk, user=self.editor)
        self.assertEqual(first.pk, second.pk)
        self.assertFalse(first.authors.exists())
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
        response = self.client.post(url, self.data(
            body=f'<img data-media-id="{private.pk}"><img data-media-id="{image.pk}" src="https://evil.test">',
        ))
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertIn(f"/medien/{image.pk}", self.article.body)
        self.assertNotIn(str(private.pk), self.article.body)
        self.assertNotIn("evil.test", self.article.body)
        self.assertEqual(list(self.article.images.all()), [image])
        anonymous = Client()
        self.assertEqual(anonymous.get(reverse("private_media", args=[image.pk])).status_code, 302)
        self.assertEqual(anonymous.get(reverse("media", args=[image.pk])).status_code, 404)
        publish_article(self.article.pk, user=self.publisher)
        response = anonymous.get(reverse("media", args=[image.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"".join(response.streaming_content))
        withdraw_article(self.article.pk, user=self.publisher)
        self.assertEqual(anonymous.get(reverse("media", args=[image.pk])).status_code, 404)

    def test_text_images_follow_the_body_on_save_and_preview(self):
        url = reverse("admin:news_article_change", args=[self.article.pk])
        preview_url = reverse("article_preview")
        first = self.image(self.editor)
        second = self.image(self.editor)
        body = f'<img data-media-id="{second.pk}"><p>Text</p><img data-media-id="{first.pk}"><img data-media-id="{second.pk}">'
        response = self.client.post(preview_url, self.data(article_id=self.article.pk, body=body))
        self.assertContains(response, f'/redaktion/medien/{second.pk}')
        self.assertFalse(self.article.images.exists())
        self.assertEqual(self.client.post(url, self.data(body=body)).status_code, 302)
        self.assertEqual(list(self.article.image_placements.values_list("media_id", flat=True)), [second.pk, first.pk])
        self.assertEqual(self.client.post(url, self.data(body=f'<img data-media-id="{first.pk}">')).status_code, 302)
        self.assertEqual(list(self.article.images.all()), [first])

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
