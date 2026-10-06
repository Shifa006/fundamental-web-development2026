from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class PlanitAuthenticationMiddleware:
    """Require authentication for Planit pages and JSON APIs.

    Django admin keeps its own authentication flow, static files remain public,
    and the login page must stay public. API callers receive JSON 401 instead
    of an HTML redirect so Fetch can handle an expired session cleanly.
    """

    PUBLIC_PREFIXES = (
        "/login/",
        "/signup/",
        "/admin/",
        "/static/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if request.user.is_authenticated or path.startswith(self.PUBLIC_PREFIXES):
            return self.get_response(request)

        if path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": {
                        "code": "authentication_required",
                        "message": "Please sign in to continue.",
                    }
                },
                status=401,
            )

        query = urlencode({"next": request.get_full_path()})
        login_url = reverse(settings.LOGIN_URL)
        return redirect(f"{login_url}?{query}")
