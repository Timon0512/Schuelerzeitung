import hashlib
import re
import secrets
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from news.models import Article
from .models import Reaction


def visitor_token(request):
    value = request.COOKIES.get(settings.HEART_COOKIE_NAME, "")
    return value if re.fullmatch(r"[A-Za-z0-9_-]{43}", value) else None


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def ensure_cookie(request, response):
    if not visitor_token(request):
        response.set_cookie(settings.HEART_COOKIE_NAME, secrets.token_urlsafe(32),
            max_age=settings.HEART_COOKIE_AGE, httponly=True, secure=settings.HEART_COOKIE_SECURE, samesite="Lax")
    return response


@transaction.atomic
def toggle_heart(slug, token):
    # Lock the article even if no reaction exists yet. Concurrent clicks serialize.
    article = get_object_or_404(Article.objects.public().select_for_update(), slug=slug)
    reaction, created = Reaction.objects.get_or_create(article=article, visitor_token_hash=token_hash(token))
    if not created:
        reaction.delete()
    return article
