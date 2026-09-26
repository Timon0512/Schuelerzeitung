"""Bound public bodies before CSRF parses multipart data; count all POST attempts."""
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from reactions.limits import consume_attempt


class InteractionLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        scope = None
        if request.method == "POST":
            if request.path == "/artikel-einreichen":
                scope = "submission"
            elif request.path.startswith("/artikel/") and request.path.endswith("/herz"):
                scope = "heart"
        if scope:
            request.sensitive_post_parameters = "__ALL__"
            allowed, retry = consume_attempt(request, scope)
            if not allowed:
                response = HttpResponse("Zu viele Versuche. Bitte warte etwas und versuche es erneut.", status=429)
                response["Retry-After"] = str(retry)
                response["Cache-Control"] = "no-store"
                return response
            limit = getattr(settings, scope.upper() + "_REQUEST_BYTES")
            try:
                length = int(request.META.get("CONTENT_LENGTH") or 0)
            except ValueError:
                return HttpResponse("Ungültige Anfrage.", status=400)
            if length < 0 or length > limit:
                return HttpResponse("Die Anfrage ist zu groß. Bitte ein kleineres Bild auswählen.", status=413)
            # Bounded read also covers missing/inaccurate Content-Length under ASGI.
            body = request.read(limit + 1)
            if len(body) > limit:
                return HttpResponse("Die Anfrage ist zu groß.", status=413)
            request._body = body
            request._stream = BytesIO(body)
            # Per-request limits leave large staff/admin forms unaffected.
            fields = sum(len(values) for _, values in request.POST.lists())
            files = sum(len(values) for _, values in request.FILES.lists())
            if fields > settings.INTERACTION_MAX_FIELDS or files > settings.INTERACTION_MAX_FILES:
                return HttpResponse("Zu viele Formularfelder oder Dateien. Bitte nur ein Bild senden.", status=400)
        return self.get_response(request)
