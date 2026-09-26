from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def require_database_configuration():
    db = settings.DATABASES["default"]
    if not all(db.get(key) for key in ("HOST", "NAME", "USER")):
        raise ImproperlyConfigured("PGHOST, PGDATABASE und PGUSER müssen ausdrücklich konfiguriert sein.")
