from io import BytesIO
from django.conf import settings
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 25_000_000


def decode_pixels(upload):
    """Ignore names/MIME claims and return validated pixels without metadata."""
    max_bytes = min(MAX_BYTES, settings.IMAGE_MAX_BYTES)
    max_pixels = min(MAX_PIXELS, settings.IMAGE_MAX_PIXELS)
    data = upload.read(max_bytes + 1)
    if not data or len(data) > max_bytes:
        raise ValidationError(f"Bitte ein Bild mit höchstens {max_bytes / 1024 / 1024:g} MB auswählen.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Erlaubt sind JPEG, PNG und WebP.")
                if source.width * source.height > max_pixels:
                    raise ValidationError(f"Das Bild darf höchstens {max_pixels / 1000000:g} Megapixel haben.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValidationError("Bitte ein unbewegtes Bild auswählen.")
                source.load()
                has_alpha = "A" in source.getbands() or "transparency" in source.info
                pixels = ImageOps.exif_transpose(source).convert("RGBA" if has_alpha else "RGB")
                fresh = Image.new(pixels.mode, pixels.size)
                fresh.paste(pixels)
                return fresh
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Das Bild ist beschädigt oder kann nicht sicher geöffnet werden.") from exc


def decode_image(upload):
    fresh = decode_pixels(upload)
    output = BytesIO()
    try:
        fresh.save(output, format="WEBP", quality=88)
    except (OSError, ValueError) as exc:
        raise ValidationError("Das Bild kann nicht als WebP gespeichert werden. Bitte die Bildabmessungen verkleinern.") from exc
    if output.tell() > min(MAX_BYTES, settings.IMAGE_MAX_BYTES):
        raise ValidationError("Das verarbeitete Bild überschreitet die erlaubte Dateigröße.")
    file = ContentFile(output.getvalue(), name="image.webp")
    file.validated_dimensions = fresh.size
    return file, fresh.width, fresh.height
