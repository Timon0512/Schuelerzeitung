"""Production settings checks in isolated subprocesses, without DB access."""
import os
import subprocess
import sys
import unittest


class DeploymentTests(unittest.TestCase):
    def run_settings(self, **overrides):
        env = dict(os.environ, DJANGO_ENV="production", DJANGO_DEBUG="false",
                   DJANGO_SECRET_KEY="test-only-" + "abcdefghij0123456789" * 4,
                   DJANGO_ALLOWED_HOSTS="zeitung.example.invalid",
                   DJANGO_CSRF_TRUSTED_ORIGINS="https://zeitung.example.invalid",
                   DJANGO_TRUST_PROXY_PROTO="true", DJANGO_HSTS_SECONDS="31536000")
        env.update(overrides)
        return subprocess.run([sys.executable, "-c", '''
import config.settings as s
from django.conf import settings
settings.configure(SECURE_PROXY_SSL_HEADER=getattr(s, "SECURE_PROXY_SSL_HEADER", None))
from django.http import HttpRequest
r = HttpRequest()
r.META["HTTP_X_FORWARDED_PROTO"] = "https"
assert r.is_secure() == (s.os.getenv("DJANGO_TRUST_PROXY_PROTO") == "true")
assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE and s.HEART_COOKIE_SECURE
assert s.SECURE_SSL_REDIRECT and not s.DEBUG
'''], env=env, capture_output=True, text=True)

    def test_secure_proxy_and_cookies(self):
        result = self.run_settings()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_untrusted_proto_ignored(self):
        result = self.run_settings(DJANGO_TRUST_PROXY_PROTO="false")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unsafe_production_configuration_rejected(self):
        for override in ({"DJANGO_DEBUG": "true"}, {"DJANGO_SECRET_KEY": "short"},
                         {"DJANGO_ALLOWED_HOSTS": "*"}, {"DJANGO_ALLOWED_HOSTS": ""},
                         {"DJANGO_ENV": "prod"},
                         {"DJANGO_CSRF_TRUSTED_ORIGINS": "http://example.invalid"}):
            with self.subTest(override=override):
                self.assertNotEqual(self.run_settings(**override).returncode, 0)
