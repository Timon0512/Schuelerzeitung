from io import BytesIO
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 25_000_000


def decode_image(upload):
    """Ignore names/MIME claims; fully decode and encode fresh pixels without metadata."""
    data = upload.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValidationError("Bitte ein Bild mit höchstens 10 MB auswählen.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Erlaubt sind JPEG, PNG und WebP.")
                if source.width * source.height > MAX_PIXELS:
                    raise ValidationError("Das Bild darf höchstens 25 Megapixel haben.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValidationError("Bitte ein unbewegtes Bild auswählen.")
                source.load()
                has_alpha = "A" in source.getbands() or "transparency" in source.info
                pixels = ImageOps.exif_transpose(source).convert("RGBA" if has_alpha else "RGB")
                fresh = Image.new(pixels.mode, pixels.size)
                fresh.paste(pixels)
                output = BytesIO()
                fresh.save(output, format="WEBP", quality=88)
                if output.tell() > MAX_BYTES:
                    raise ValidationError("Das verarbeitete Bild überschreitet 10 MB.")
                return ContentFile(output.getvalue(), name="image.webp"), fresh.width, fresh.height
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Das Bild ist beschädigt oder kann nicht sicher geöffnet werden.") from exc
