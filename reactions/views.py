from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from .services import ensure_cookie, toggle_heart, visitor_token


@require_POST
def heart(request, slug):
    token = visitor_token(request)
    if token is None:
        # A confirmed cookie round trip is required; concurrent first POSTs cannot mint hearts.
        response = HttpResponse("Bitte Cookies zulassen, den Artikel neu laden und erneut klicken.", status=400)
        response["Cache-Control"] = "no-store"
        return ensure_cookie(request, response)
    article = toggle_heart(slug, token)
    response = HttpResponseRedirect(reverse("article", args=[article.slug]))
    response["Cache-Control"] = "no-store"
    return response
