from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from news.public import public_render
from news.submission_ui import SubmissionUIForm
from .services import receive_submission


@sensitive_post_parameters()
@require_http_methods(["GET", "HEAD", "POST"])
def submission(request):
    form = SubmissionUIForm(request.POST if request.method == "POST" else None,
                            request.FILES if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        receive_submission(form)
        request.session["submission_received"] = True
        response = HttpResponseRedirect(reverse("submission"))
        response["Cache-Control"] = "no-store"
        return response
    received = request.session.pop("submission_received", False) if request.method == "GET" else False
    return public_render(request, "news/submission.html", {
        "title": "Artikel einreichen", "form": form, "noindex": True,
        "submission_enabled": True, "submission_received": received,
    }, status=400 if form.is_bound else 200)
