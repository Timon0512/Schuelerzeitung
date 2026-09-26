import os
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "local-check-only-not-for-serving")
import django
django.setup()

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.http import Http404
from django.test import override_settings
from news.image_variants import encode_variants, attach_variants, image_attributes, stored_files, delete_files, save_upload
from news.models import Article, Media
from news.views import image_response
from news.content import clean_body


def upload(size=(2400, 1600), mode="RGB"):
    output = BytesIO()
    Image.new(mode, size, (24, 90, 130, 100) if mode == "RGBA" else (24, 90, 130)).save(output, "PNG")
    return ContentFile(output.getvalue(), name="photo.png")


class ImageVariantTests(unittest.TestCase):
    def test_two_sizes_and_transparency(self):
        variants = encode_variants(upload(mode="RGBA"))
        for name, size in (("small", (640, 427)), ("large", (1920, 1280))):
            file, width, height = variants[name]
            self.assertEqual((width, height), size)
            with Image.open(file) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.size, size)
                self.assertIn("A", image.getbands())
                self.assertFalse(image.getexif())

    def test_small_images_share_file_without_upscaling(self):
        variants = encode_variants(upload((320, 480)))
        self.assertIs(variants["small"], variants["large"])
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            media = Media()
            created = []
            attach_variants(media, variants, created)
            self.assertEqual(len(created), 1)
            self.assertEqual(media.small_file.name, media.large_file.name)
            self.assertEqual(media.large_width, 320)
            self.assertEqual(media.large_height, 480)
            self.assertEqual(image_attributes(media)["srcset"].count("320w"), 1)
            delete_files(stored_files(media))
            self.assertFalse(media.small_file.storage.exists(media.small_file.name))

    def test_portrait_and_exif_orientation(self):
        data = BytesIO()
        photo = Image.new("RGB", (1600, 2400), "orange")
        exif = Image.Exif()
        exif[274] = 6
        photo.save(data, "JPEG", exif=exif)
        variants = encode_variants(ContentFile(data.getvalue()))
        self.assertEqual(variants["large"][1:], (1920, 1280))
        with Image.open(variants["large"][0]) as result:
            self.assertFalse(result.getexif())

    def test_invalid_and_pixel_limits(self):
        with self.assertRaises(ValidationError):
            encode_variants(ContentFile(b"not a photo"))
        with override_settings(IMAGE_MAX_PIXELS=100), self.assertRaises(ValidationError):
            encode_variants(upload((20, 20)))

    def test_rendered_text_images_have_private_responsive_urls(self):
        media = Media(width=2400, height=1600, alt_text='A "photo"', small_file="small.webp", small_width=640,
                      large_file="large.webp", large_width=1920)
        markup = clean_body(f'<img data-media-id="{media.pk}" srcset="https://evil.test/a 640w">', [media], private=True, render=True)
        self.assertIn(f'/redaktion/medien/{media.pk}/large', markup)
        self.assertIn(f'/redaktion/medien/{media.pk}/small 640w', markup)
        self.assertNotIn("evil.test", markup)
        self.assertIn('loading="lazy"', markup)
        self.assertIn("&quot;photo&quot;", markup)

    def test_legacy_fallback_and_unknown_variant(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            media = Media(mime_type="image/png")
            media.file.save("legacy.png", upload((20, 20)), save=False)
            response = image_response(media, "small")
            self.assertEqual(response["Content-Type"], "image/png")
            response.close()
            self.assertEqual(image_attributes(media)["srcset"], "")
            with self.assertRaises(Http404):
                image_response(media, "arbitrary")

    def test_focus_bounds(self):
        for name in ("hero_focus_x", "hero_focus_y"):
            field = Article._meta.get_field(name)
            for bad in (-1, 101):
                with self.assertRaises(ValidationError):
                    field.clean(bad, Article())
            self.assertEqual(field.clean(0, Article()), 0)
            self.assertEqual(field.clean(100, Article()), 100)

    def test_write_failure_removes_new_files(self):
        from contextlib import nullcontext
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            media = Media(file=upload((32, 24)))
            with patch("news.image_variants.transaction.atomic", return_value=nullcontext()), \
                 patch("news.models.content_lock"), \
                 patch("news.models.Media.objects.filter") as query, \
                 patch("news.image_variants.models.Model.save", side_effect=RuntimeError("write failed")):
                query.return_value.first.return_value = None
                with self.assertRaises(RuntimeError):
                    save_upload(media, (), {})
            for storage, name in stored_files(media):
                self.assertFalse(storage.exists(name))
