from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class MarkupAuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.buttons_without_type = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "button" and "type" not in attrs:
            self.buttons_without_type.append(attrs.get("id") or attrs.get("class") or "button")


class FrontendContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="frontend-user",
            password="TestPass123!",
        )
        self.client.force_login(self.user)

    def test_bootstrap_is_bundled_locally(self):
        self.assertIsNotNone(finders.find("vendor/bootstrap/bootstrap.min.css"))
        self.assertIsNotNone(finders.find("vendor/bootstrap/bootstrap.bundle.min.js"))

        response = self.client.get(reverse("today"))
        html = response.content.decode()
        self.assertIn("/static/vendor/bootstrap/bootstrap.min.css", html)
        self.assertIn("/static/vendor/bootstrap/bootstrap.bundle.min.js", html)
        self.assertNotIn("cdn.jsdelivr.net/npm/bootstrap", html)

    def test_main_pages_have_unique_ids_and_typed_buttons(self):
        for route in ("today", "tasks", "courses", "projects"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)

                parser = MarkupAuditParser()
                parser.feed(response.content.decode())

                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertEqual(parser.buttons_without_type, [])

    def test_mobile_css_does_not_hide_all_soft_buttons(self):
        css_path = Path(settings.BASE_DIR) / "planner/static/planner/css/style.css"
        css = css_path.read_text()
        self.assertNotIn(".soft-button:not(.is-active)", css)
    def test_pastel_quest_today_hooks_are_rendered(self):
        response = self.client.get(reverse("today"))
        html = response.content.decode()

        self.assertIn('id="todayProgressRing"', html)
        self.assertIn('id="progressPercent"', html)
        self.assertIn('class="today-dashboard"', html)
        self.assertGreaterEqual(html.count("data-exam-toggle"), 2)

    def test_pastel_quest_tasks_hooks_are_rendered(self):
        response = self.client.get(reverse("tasks"))
        html = response.content.decode()

        self.assertIn('id="weekRange"', html)
        self.assertIn('class="week-board game-card"', html)
        self.assertIn('id="weekGrid"', html)
        self.assertIn('id="taskSearch"', html)

    def test_base_uses_local_assets_only_for_framework_and_no_google_fonts(self):
        response = self.client.get(reverse("today"))
        html = response.content.decode()

        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("fonts.gstatic.com", html)
        self.assertIn('/static/vendor/bootstrap/bootstrap.min.css', html)
        self.assertIn('/static/vendor/bootstrap/bootstrap.bundle.min.js', html)


    def test_semantic_navigation_and_presentation_controls_are_rendered(self):
        response = self.client.get(reverse("today"))
        html = response.content.decode()
        self.assertIn('class="nav-list"', html)
        self.assertIn('<li>', html)
        self.assertIn('data-theme-toggle', html)
        self.assertIn('action="/logout/"', html)
        self.assertIn('id="topFocusTitle"', html)

    def test_login_page_has_required_hooks(self):
        self.client.logout()
        response = self.client.get(reverse("login"))
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="loginUsername"', html)
        self.assertIn('id="loginPassword"', html)
        self.assertIn('id="passwordToggle"', html)
        self.assertIn('data-theme-toggle', html)
        self.assertIn('/static/planner/js/theme.js', html)
        self.assertIn('/static/planner/js/login.js', html)
