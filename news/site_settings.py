from django.db import DatabaseError

from .models import SiteSetting


def get_site_settings(*, tolerate_database_error=False):
    try:
        return SiteSetting.objects.select_related("logo").first() or SiteSetting()
    except DatabaseError:
        if not tolerate_database_error:
            raise
        return SiteSetting()
