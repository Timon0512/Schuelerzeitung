import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.runner import DiscoverRunner


def validate_test_database():
    db = settings.DATABASES["default"]
    name = db["TEST"].get("NAME", "")
    if (settings.ENVIRONMENT != "development" or not db["HOST"] or not db["NAME"]
            or not name or name == db["NAME"] or not name.endswith("_test")
            or os.getenv("KAKTUS_TEST_DATABASE_CONFIRMED") != "true"):
        raise ImproperlyConfigured(
            "Test gesperrt: Entwicklungsverbindung und separate, ausdrücklich als entbehrlich "
            "bestätigte PGTESTDATABASE (*_test) erforderlich. Kein SQLite-Fallback.")


class SafePostgresRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        validate_test_database()
        return super().setup_databases(**kwargs)
