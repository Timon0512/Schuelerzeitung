from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Media
from .image_variants import stored_files, delete_files


@receiver(post_delete, sender=Media)
def remove_media_files(sender, instance, **kwargs):
    files = stored_files(instance)
    transaction.on_commit(lambda: delete_files(files), robust=True)
