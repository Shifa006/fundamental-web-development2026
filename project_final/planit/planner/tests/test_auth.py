from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student",
            password="SecurePass123!",
        )

    def test_login_page_is_public(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SIGN IN")

    def test_main_page_redirects_to_login_when_signed_out(self):
        response = self.client.get(reverse("today"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/?next="))

    def test_api_returns_json_401_when_signed_out(self):
        response = self.client.get(reverse("api_tasks"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_wrong_password_shows_error_without_logging_in(self):
        response = self.client.post(
            reverse("login"),
            {"username": "student", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect username or password.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_correct_login_creates_session_and_redirects(self):
        response = self.client.post(
            reverse("login"),
            {"username": "student", "password": "SecurePass123!"},
        )
        self.assertRedirects(response, reverse("today"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)

    def test_safe_next_parameter_is_respected(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "student",
                "password": "SecurePass123!",
                "next": reverse("projects"),
            },
        )
        self.assertRedirects(response, reverse("projects"))

    def test_external_next_parameter_is_ignored(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "student",
                "password": "SecurePass123!",
                "next": "https://example.com/steal-session",
            },
        )
        self.assertRedirects(response, reverse("today"))

    def test_logout_requires_post_and_clears_session(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse("logout"))
        self.assertEqual(get_response.status_code, 405)

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_form_is_csrf_protected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("login"),
            {"username": "student", "password": "SecurePass123!"},
        )
        self.assertEqual(response.status_code, 403)


class SignUpAndIsolationTests(TestCase):
    VALID = {
        "username": "newbie",
        "email": "newbie@example.com",
        "password1": "Str0ng!Pass#9",
        "password2": "Str0ng!Pass#9",
    }

    def test_signup_creates_hashed_user_and_logs_in(self):
        response = self.client.post(reverse("signup"), self.VALID)
        self.assertRedirects(response, reverse("today"), fetch_redirect_response=False)
        user = get_user_model().objects.get(username="newbie")
        self.assertNotEqual(user.password, self.VALID["password1"])
        self.assertTrue(user.password.startswith(("pbkdf2_", "argon2", "scrypt")))
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_rejected_case_insensitively(self):
        get_user_model().objects.create_user("a", "Newbie@Example.com", "Str0ng!Pass#9")
        response = self.client.post(reverse("signup"), self.VALID)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered")

    def test_duplicate_username_rejected(self):
        get_user_model().objects.create_user("newbie", "x@example.com", "Str0ng!Pass#9")
        self.assertEqual(self.client.post(reverse("signup"), self.VALID).status_code, 200)
        self.assertEqual(get_user_model().objects.filter(username="newbie").count(), 1)

    def test_weak_and_mismatched_passwords_rejected(self):
        for p1, p2 in (("password", "password"), ("alllowercase1!", "alllowercase1!"), ("Str0ng!Pass#9", "Different1!")):
            data = {**self.VALID, "password1": p1, "password2": p2}
            self.assertEqual(self.client.post(reverse("signup"), data).status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="newbie").exists())

    def test_users_cannot_see_or_edit_each_others_data(self):
        User = get_user_model()
        alice = User.objects.create_user("alice", password="Str0ng!Pass#9")
        bob = User.objects.create_user("bob", password="Str0ng!Pass#9")
        self.client.force_login(alice)
        created = self.client.post(
            reverse("api_tasks"), data='{"title": "Alice secret"}', content_type="application/json"
        )
        self.assertIn(created.status_code, (200, 201))
        task_id = created.json().get("task", created.json()).get("id")

        other = Client()
        other.force_login(bob)
        self.assertNotIn("Alice secret", other.get(reverse("api_tasks")).content.decode())
        self.assertEqual(other.delete(reverse("api_task_detail", args=[task_id])).status_code, 404)
