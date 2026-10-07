import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from planner.forms import SignUpForm
from planner.password_validators import ComplexityValidator
from django.core.exceptions import ValidationError


class SignupHtmlHintsTests(TestCase):
    def test_signup_page_renders_password_pattern_and_length_hints(self):
        html = self.client.get(reverse("signup")).content.decode()
        self.assertIn("pattern=", html)
        self.assertIn('minlength="8"', html)
        self.assertIn("title=", html)

    def test_signup_form_is_not_marked_novalidate(self):
        html = self.client.get(reverse("signup")).content.decode()
        self.assertNotIn("novalidate", html)

    def test_html_pattern_agrees_with_server_complexity_rule(self):
        pattern = re.compile(SignUpForm.PASSWORD_PATTERN)
        for password, ok in [
            ("Abcdef1!", True),
            ("alllowercase1!", False),
            ("ALLUPPERCASE1!", False),
            ("NoDigits!!", False),
            ("NoSpecial12", False),
            ("Ab1!", False),
        ]:
            browser_ok = pattern.fullmatch(password) is not None
            try:
                ComplexityValidator().validate(password)
                server_ok = True
            except ValidationError:
                server_ok = False
            if len(password) >= 8:
                self.assertEqual(browser_ok, server_ok, password)
            self.assertEqual(browser_ok, ok, password)

    def test_server_still_rejects_weak_password_when_html_is_bypassed(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "bypass", "email": "b@example.com",
             "password1": "alllowercase1!", "password2": "alllowercase1!"},
        )
        self.assertEqual(response.status_code, 200)


class StatusCountReduceTests(TestCase):
    def test_tasks_js_uses_reduce_for_status_counts(self):
        js = (Path(settings.BASE_DIR) / "planner/static/planner/js/tasks.js").read_text()
        self.assertIn("function countByStatus", js)
        self.assertIn(".reduce(", js)
        self.assertIn("updateStatusCounts();", js)
