import os
import unittest
import uuid
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "local-check-only-not-for-serving")
import django
django.setup()
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, PngImagePlugin
from news.content import clean_body
from news.uploads import decode_image, MAX_BYTES
from news.services import require_editor, require_publisher
from django.template.loader import get_template
from news.models import Article


class ContentBoundaryTests(unittest.TestCase):
    def test_admin_and_preview_templates_compile(self):
        for name in ("admin/base_site.html", "admin/news/article/change_form.html", "news/preview.html"):
            get_template(name)
        rendered = get_template("admin/news/article/submit_line.html").render({
            "opts": Article._meta, "original": Article(pk=1), "show_save": True,
            "show_close": True, "show_delete_link": True,
        })
        self.assertIn("Entwurf speichern", rendered)
        self.assertIn("/admin/news/article/1/delete/", rendered)

    def test_xss_and_protocols(self):
        value = '<script>alert(1)</script><p onclick="bad()">Hallo</p><a href="javascript:alert(1)">x</a><a href="https://example.org">gut</a><iframe src="https://evil.test"></iframe>'
        result = clean_body(value)
        for bad in ("script", "onclick", "javascript", "iframe"):
            self.assertNotIn(bad, result)
        self.assertIn('href="https://example.org"', result)

    def test_images_require_explicit_grant_and_ignore_all_client_attributes(self):
        image = SimpleNamespace(pk=uuid.uuid4(), alt_text='Ein "Bild"', caption="<privat>")
        value = f'<img src="https://evil.test" onerror="bad()" data-media-id="{image.pk}"><img src="/medien/{uuid.uuid4()}">'
        self.assertNotIn("img", clean_body(value))
        result = clean_body(value, [image])
        self.assertEqual(result.count("<img"), 1)
        self.assertNotIn("evil", result)
        self.assertNotIn("onerror", result)
        self.assertIn("&quot;Bild&quot;", result)
        self.assertEqual(clean_body(result, [image]), result)
        preview = clean_body(value, [image], private=True)
        self.assertIn("/redaktion/medien/", preview)
        self.assertIn("&lt;privat&gt;", preview)

    def test_entity_text_stays_escaped(self):
        self.assertNotIn("<script", clean_body("<p>&lt;script&gt; &amp; &#60;img&#62;</p>"))

    def test_permission_boundaries(self):
        user = SimpleNamespace(is_active=True, is_staff=False, has_perm=lambda p: False)
        for check in (require_editor, require_publisher):
            with self.assertRaises(PermissionDenied):
                check(user)


class UploadTests(unittest.TestCase):
    def test_reencoding_strips_metadata_and_ignores_extension(self):
        source = BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Private", "secret-location")
        Image.new("RGB", (12, 8), "red").save(source, "PNG", pnginfo=metadata)
        file, width, height = decode_image(SimpleUploadedFile("wrong.exe", source.getvalue(), "text/html"))
        self.assertEqual((width, height), (12, 8))
        encoded = file.read()
        with Image.open(BytesIO(encoded)) as result:
            self.assertEqual(result.format, "WEBP")
            self.assertNotIn("Private", result.info)
        self.assertNotIn(b"secret-location", encoded)

    def test_invalid_svg_truncated_and_oversize_rejected(self):
        for data in (b'<svg xmlns="http://www.w3.org/2000/svg"/>', b'\x89PNG\r\n', b'x' * (MAX_BYTES + 1)):
            with self.subTest(size=len(data)), self.assertRaises(ValidationError):
                decode_image(BytesIO(data))

    def test_pixel_limit_and_animation(self):
        data = BytesIO()
        Image.new("RGB", (5, 5)).save(data, "PNG")
        with patch("news.uploads.MAX_PIXELS", 24), self.assertRaises(ValidationError):
            decode_image(BytesIO(data.getvalue()))
        data = BytesIO()
        Image.new("RGB", (5, 5), "red").save(data, "WEBP", save_all=True, append_images=[Image.new("RGB", (5, 5), "blue")], duration=100)
        with self.assertRaises(ValidationError):
            decode_image(BytesIO(data.getvalue()))
