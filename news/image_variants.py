"""Two precomputed WebP sizes; storage is never publicly addressable."""
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.urls import reverse

from .uploads import decode_image, decode_pixels

VARIANTS = (("small", 640), ("large", 1920))
VARIANT_FIELDS = [f"{name}_{suffix}" for name, _ in VARIANTS for suffix in ("file", "width", "height", "size")]


def encode_variants(file):
    file.seek(0)
    # Reuse the upload security boundary for legacy files as well.
    source = decode_pixels(file)
    result = {}
    with source:
        for name, limit in VARIANTS:
            width = min(source.width, limit)
            height = max(1, round(source.height * width / source.width))
            if name == "large" and width == result["small"][1]:
                result[name] = result["small"]
                continue
            pixels = source.resize((width, height), Image.Resampling.LANCZOS)
            output = BytesIO()
            pixels.save(output, "WEBP", quality=82, method=6)
            result[name] = (ContentFile(output.getvalue(), name=f"{name}.webp"), width, height)
    file.seek(0)
    return result


def stored_files(media):
    return [(field.storage, field.name) for field in (media.file, media.small_file, media.large_file) if field.name]


def delete_files(files):
    seen = set()
    for storage, name in files:
        key = (id(storage), name)
        if key not in seen:
            storage.delete(name)
            seen.add(key)


def attach_variants(media, encoded, created):
    for name, _ in VARIANTS:
        file, width, height = encoded[name]
        field = getattr(media, f"{name}_file")
        if name == "large" and encoded[name] is encoded["small"]:
            field.name = media.small_file.name
        else:
            field.save(file.name, file, save=False)
            created.append((field.storage, field.name))
        for suffix, value in (("width", width), ("height", height), ("size", file.size)):
            setattr(media, f"{name}_{suffix}", value)


def save_upload(media, args, kwargs):
    from .models import Media, content_lock
    upload = media.file.file
    upload.seek(0)
    if hasattr(upload, "validated_dimensions"):
        clean = upload
        width, height = upload.validated_dimensions
    else:
        clean, width, height = decode_image(upload)
    encoded = encode_variants(clean)
    created = []
    try:
        with transaction.atomic():
            content_lock()
            previous = Media.objects.filter(pk=media.pk).first()
            old = stored_files(previous) if previous else []
            media.file.save(clean.name, clean, save=False)
            created.append((media.file.storage, media.file.name))
            media.width, media.height = width, height
            media.size, media.mime_type = clean.size, "image/webp"
            attach_variants(media, encoded, created)
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | set(VARIANT_FIELDS) | {"width", "height", "size", "mime_type"}
            models.Model.save(media, *args, **kwargs)
            transaction.on_commit(lambda: delete_files(old), robust=True)
    except Exception:
        delete_files(created)
        raise


def image_attributes(media, *, private=False):
    """Safe generated attributes, shared by templates and sanitized text images."""
    route = "private_media" if private else "media"
    base = reverse(route, args=[media.pk])
    candidates = []
    for name, _ in VARIANTS:
        if getattr(media, f"{name}_file", None):
            width = getattr(media, f"{name}_width")
            if not any(w == width for _, w in candidates):
                candidates.append((reverse(route + "_variant", args=[media.pk, name]), width))
    return {
        "src": reverse(route + "_variant", args=[media.pk, "large"]) if getattr(media, "large_file", None) else base,
        "srcset": ", ".join(f"{url} {width}w" for url, width in candidates),
    }
