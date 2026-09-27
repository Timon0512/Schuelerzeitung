import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY muss lokal gesetzt sein.")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "django.contrib.sitemaps",
    "accounts.apps.AccountsConfig", "news", "submissions", "reactions",
]
MIDDLEWARE = [
    "config.interaction_limits.InteractionLimitMiddleware",
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"],
              "APP_DIRS": True, "OPTIONS": {"context_processors": [
                  "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
                  "django.contrib.messages.context_processors.messages",
                  "news.context_processors.admin_submission_notifications"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql", "HOST": os.getenv("PGHOST", ""),
    "PORT": os.getenv("PGPORT", "5432"), "NAME": os.getenv("PGDATABASE", ""),
    "USER": os.getenv("PGUSER", ""), "PASSWORD": os.getenv("PGPASSWORD", ""),
    "OPTIONS": {"sslmode": os.getenv("PGSSLMODE", "prefer"), "connect_timeout": 5},
    "TEST": {"NAME": os.getenv("PGTESTDATABASE", "")},
}}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation." + name} for name in [
    "UserAttributeSimilarityValidator", "MinimumLengthValidator", "CommonPasswordValidator", "NumericPasswordValidator"]]
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.getenv("DJANGO_STATIC_ROOT", str(BASE_DIR / "staticfiles")))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_ROOT = Path(os.getenv("DJANGO_MEDIA_ROOT", str(BASE_DIR / "media" / "private")))
# No public filesystem URL or development static() mapping for uploaded files.
MEDIA_URL = "/protected-files/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TEST_RUNNER = "config.test_runner.SafePostgresRunner"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
if ENVIRONMENT == "production":
    if DEBUG:
        raise ImproperlyConfigured("DEBUG ist in Produktion verboten.")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
CSRF_TRUSTED_ORIGINS = list(filter(None, os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")))
if os.getenv("DJANGO_TRUST_PROXY_PROTO", "false").lower() == "true":
    # Only enable behind an isolated proxy that overwrites this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
if ENVIRONMENT not in ("development", "production"):
    raise ImproperlyConfigured("DJANGO_ENV muss development oder production sein.")
if ENVIRONMENT == "production":
    if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
        raise ImproperlyConfigured("Produktion benötigt einen starken eigenen SECRET_KEY.")
    if not os.getenv("DJANGO_ALLOWED_HOSTS") or any(not h.strip() or h.startswith(".") or "*" in h for h in ALLOWED_HOSTS):
        raise ImproperlyConfigured("Produktion benötigt explizite erlaubte Hosts ohne Wildcards.")
    if any(not origin.startswith("https://") or "*" in origin for origin in CSRF_TRUSTED_ORIGINS):
        raise ImproperlyConfigured("CSRF-Origins müssen explizite HTTPS-Origins sein.")

# Public interaction limits. Upload ceilings also remain enforced by Media constraints.
def positive_setting(name, default):
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ImproperlyConfigured(f"{name} muss positiv sein.")
    return value

SUBMISSION_NAME_LIMIT = min(120, positive_setting("SUBMISSION_NAME_LIMIT", 120))
SUBMISSION_CLASS_LIMIT = min(40, positive_setting("SUBMISSION_CLASS_LIMIT", 40))
SUBMISSION_TITLE_LIMIT = min(200, positive_setting("SUBMISSION_TITLE_LIMIT", 200))
SUBMISSION_BODY_LIMIT = min(50000, positive_setting("SUBMISSION_BODY_LIMIT", 50000))
IMAGE_MAX_BYTES = min(10 * 1024 * 1024, positive_setting("IMAGE_MAX_BYTES", 10 * 1024 * 1024))
IMAGE_MAX_PIXELS = min(25000000, positive_setting("IMAGE_MAX_PIXELS", 25000000))
SUBMISSION_REQUEST_BYTES = positive_setting("SUBMISSION_REQUEST_BYTES", 11 * 1024 * 1024)
HEART_REQUEST_BYTES = positive_setting("HEART_REQUEST_BYTES", 4096)
SUBMISSION_RATE_LIMIT = positive_setting("SUBMISSION_RATE_LIMIT", 5)
SUBMISSION_RATE_SECONDS = positive_setting("SUBMISSION_RATE_SECONDS", 3600)
HEART_RATE_LIMIT = positive_setting("HEART_RATE_LIMIT", 60)
HEART_RATE_SECONDS = positive_setting("HEART_RATE_SECONDS", 60)
TRUSTED_PROXY_NETWORKS = list(filter(None, os.getenv("TRUSTED_PROXY_NETWORKS", "").split(",")))
HEART_COOKIE_NAME = "kaktus_visitor"
HEART_COOKIE_AGE = positive_setting("HEART_COOKIE_AGE", 365 * 86400)
HEART_COOKIE_SECURE = ENVIRONMENT == "production"
SUBMISSION_RETENTION_DAYS = int(os.getenv("SUBMISSION_RETENTION_DAYS", "0"))
REACTION_RETENTION_DAYS = int(os.getenv("REACTION_RETENTION_DAYS", "0"))
RETENTION_CONFIRMED = os.getenv("RETENTION_CONFIRMED", "false").lower() == "true"
INTERACTION_MAX_FIELDS = positive_setting("INTERACTION_MAX_FIELDS", 20)
INTERACTION_MAX_FILES = 1

if SUBMISSION_RETENTION_DAYS < 0 or REACTION_RETENTION_DAYS < 0:
    raise ImproperlyConfigured("Aufbewahrungsfristen dürfen nicht negativ sein.")
