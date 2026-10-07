import re

from django.core.exceptions import ValidationError


class ComplexityValidator:
    """Require upper-case, lower-case, a digit and a special character."""

    RULES = (
        (r"[A-Z]", "an uppercase letter (A-Z)"),
        (r"[a-z]", "a lowercase letter (a-z)"),
        (r"\d", "a number (0-9)"),
        (r"[^A-Za-z0-9\s]", "a special character (e.g. ! @ # ?)"),
    )

    def validate(self, password, user=None):
        missing = [text for pattern, text in self.RULES if not re.search(pattern, password)]
        if missing:
            raise ValidationError(
                "Password must also contain " + ", ".join(missing) + ".",
                code="password_too_simple",
            )

    def get_help_text(self):
        return "Use 8+ characters with upper-case, lower-case, a number and a special character."


class MaxLengthValidator:
    """Reject very long passwords (matches the maxlength on the sign-up form)."""

    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                f"Password must be at most {self.max_length} characters.",
                code="password_too_long",
            )

    def get_help_text(self):
        return f"Use at most {self.max_length} characters."
