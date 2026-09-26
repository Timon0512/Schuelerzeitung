"""Database-free checks; run with unittest, never a substitute for PostgreSQL tests."""
import os
import unittest
from copy import deepcopy
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "unit-test-configuration-only")
import django
django.setup()
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.migrations.loader import MigrationLoader
from django.test import override_settings
from config.db_safety import require_database_configuration
from config.test_runner import validate_test_database


class ConfigurationTests(unittest.TestCase):
    def database(self):
        db = deepcopy(settings.DATABASES)
        db["default"].update(HOST="example.invalid", NAME="kaktus_dev", USER="kaktus")
        db["default"]["TEST"]["NAME"] = "kaktus_test"
        return db

    def test_missing_confirmation_blocks_tests(self):
        with override_settings(DATABASES=self.database(), ENVIRONMENT="development"), patch.dict(os.environ, {"KAKTUS_TEST_DATABASE_CONFIRMED": "false"}):
            with self.assertRaises(ImproperlyConfigured):
                validate_test_database()

    def test_same_database_and_production_are_blocked(self):
        db = self.database()
        db["default"]["NAME"] = "kaktus_test"
        with override_settings(DATABASES=db, ENVIRONMENT="development"), patch.dict(os.environ, {"KAKTUS_TEST_DATABASE_CONFIRMED": "true"}):
            with self.assertRaises(ImproperlyConfigured):
                validate_test_database()
        with override_settings(DATABASES=self.database(), ENVIRONMENT="production"), patch.dict(os.environ, {"KAKTUS_TEST_DATABASE_CONFIRMED": "true"}):
            with self.assertRaises(ImproperlyConfigured):
                validate_test_database()

    def test_explicit_disposable_database_accepted(self):
        with override_settings(DATABASES=self.database(), ENVIRONMENT="development"), patch.dict(os.environ, {"KAKTUS_TEST_DATABASE_CONFIRMED": "true"}):
            validate_test_database()

    def test_missing_connection_blocks_mutating_commands(self):
        db = self.database()
        db["default"]["HOST"] = ""
        with override_settings(DATABASES=db):
            with self.assertRaises(ImproperlyConfigured):
                require_database_configuration()

    def test_initial_user_migration_and_graph(self):
        loader = MigrationLoader(None)
        loader.graph.validate_consistency()
        loader.graph.ensure_not_cyclic()
        self.assertIn(("accounts", "0001_initial"), loader.graph.nodes)
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")


if __name__ == "__main__":
    unittest.main()
