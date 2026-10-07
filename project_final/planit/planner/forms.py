from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    """Sign-up with a required, case-insensitively unique e-mail.

    Password rules come from settings.AUTH_PASSWORD_VALIDATORS and passwords
    are stored hashed by Django (never in plain text).
    """

    email = forms.EmailField(max_length=254)

    # HTML5 hints give immediate browser feedback. The Django validators in
    # settings.AUTH_PASSWORD_VALIDATORS stay the authority on the server because
    # browser checks can be bypassed.
    PASSWORD_PATTERN = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}"
    PASSWORD_TITLE = (
        "At least 8 characters with an upper-case letter, a lower-case letter, "
        "a number and a special character."
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "minlength": "8",
                "maxlength": "128",
                "pattern": self.PASSWORD_PATTERN,
                "title": self.PASSWORD_TITLE,
            }
        )
        self.fields["password2"].widget.attrs.update(
            {"minlength": "8", "maxlength": "128"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This e-mail is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
