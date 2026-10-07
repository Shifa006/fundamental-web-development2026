import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from planner import modules
from planner.domain import ExamItem, GeneralItem
from planner.models import Assessment, Subject, Task, UserSettings
from planner.services import (
    day_dots,
    default_assessments,
    month_bounds,
    plan_review_tasks,
    should_suggest_exam_mode,
)

TODAY = date(2026, 10, 6)
PATCH_TODAY = "django.utils.timezone.localdate"


def post_json(client, url, data, method="post"):
    return getattr(client, method)(url, data=json.dumps(data), content_type="application/json")


class PureFunctionTests(TestCase):
    def test_month_bounds_handle_leap_year_and_december(self):
        self.assertEqual(month_bounds(2028, 2), (date(2028, 2, 1), date(2028, 2, 29)))
        self.assertEqual(month_bounds(2026, 12), (date(2026, 12, 1), date(2026, 12, 31)))

    def test_plan_review_tasks_skips_past_dates(self):
        exam = TODAY + timedelta(days=5)
        planned = plan_review_tasks("Midterm", exam, TODAY)
        self.assertEqual([p["due_date"] for p in planned], [exam - timedelta(days=3), exam - timedelta(days=1)])
        self.assertEqual(planned[0]["title"], "Review: Midterm")

    def test_plan_review_tasks_exam_tomorrow_and_today(self):
        self.assertEqual(plan_review_tasks("X", TODAY + timedelta(days=1), TODAY), [])
        self.assertEqual(plan_review_tasks("X", TODAY, TODAY), [])
        self.assertEqual(len(plan_review_tasks("X", TODAY + timedelta(days=2), TODAY)), 1)

    def test_default_assessments_total_100(self):
        self.assertEqual(sum(row["weight"] for row in default_assessments()), 100)

    def test_suggest_exam_mode_boundaries(self):
        def exam(days, completed=False):
            return ExamItem(1, "E", "academic", "exam", "normal", TODAY + timedelta(days=days), completed)
        self.assertTrue(should_suggest_exam_mode([exam(14)], TODAY))
        self.assertFalse(should_suggest_exam_mode([exam(15)], TODAY))
        self.assertFalse(should_suggest_exam_mode([exam(3, completed=True)], TODAY))
        self.assertFalse(should_suggest_exam_mode([exam(-1)], TODAY))

    def test_day_dots_limit_and_order(self):
        items = [
            GeneralItem(1, "a", "academic", "general", "normal", TODAY, False),
            ExamItem(2, "e", "academic", "exam", "normal", TODAY, False),
            GeneralItem(3, "p", "personal", "general", "normal", TODAY, False),
            GeneralItem(4, "o", "academic", "general", "normal", TODAY - timedelta(days=1), False),
        ]
        self.assertEqual(day_dots(items, TODAY), ["exam", "overdue", "academic"])


class V13ApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("v13", password="Str0ng!Pass#9")
        self.client.force_login(self.user)
        self.subject = Subject.objects.create(owner=self.user, name="Web", semester="1/2026")

    def task(self, title, days, **kwargs):
        defaults = dict(owner=self.user, title=title, area="academic", kind="general",
                        priority="normal", due_date=TODAY + timedelta(days=days))
        defaults.update(kwargs)
        return Task.objects.create(**defaults)

    # ---- month ----
    def test_month_returns_every_day_and_weekday(self):
        with patch(PATCH_TODAY, return_value=TODAY):
            data = self.client.get(reverse("api_month"), {"year": 2026, "month": 10}).json()
        self.assertEqual(len(data["days"]), 31)
        self.assertEqual(data["first_weekday"], 3)  # Thursday, Monday = 0
        self.assertEqual(data["meta"]["today"], "2026-10-06")

    def test_month_february_leap_year(self):
        with patch(PATCH_TODAY, return_value=TODAY):
            data = self.client.get(reverse("api_month"), {"year": 2028, "month": 2}).json()
        self.assertEqual(len(data["days"]), 29)

    def test_month_counts_dots_and_filters(self):
        self.task("Exam", 3, kind="exam")
        for i in range(5):
            self.task(f"T{i}", 3)
        self.task("Me", 3, area="personal", subject=None)
        with patch(PATCH_TODAY, return_value=TODAY):
            data = self.client.get(reverse("api_month"), {"year": 2026, "month": 10}).json()
            personal = self.client.get(reverse("api_month"), {"year": 2026, "month": 10, "area": "personal"}).json()
        day = next(d for d in data["days"] if d["date"] == "2026-10-09")
        self.assertEqual(day["counts"]["total"], 7)
        self.assertEqual(day["counts"]["exam"], 1)
        self.assertEqual(len(day["dots"]), 3)
        pday = next(d for d in personal["days"] if d["date"] == "2026-10-09")
        self.assertEqual(pday["counts"]["total"], 1)

    def test_month_overdue_before_month_is_counted_separately(self):
        self.task("Old", -40)
        with patch(PATCH_TODAY, return_value=TODAY):
            data = self.client.get(reverse("api_month"), {"year": 2026, "month": 10}).json()
        self.assertEqual(data["overdue_before_month"], 1)
        self.assertTrue(all(d["counts"]["total"] == 0 for d in data["days"]))

    def test_month_bad_parameters_are_400(self):
        for params in ({"month": 13}, {"month": 0}, {"year": 1999}, {"year": "x"}, {"area": "nope"}):
            self.assertEqual(self.client.get(reverse("api_month"), params).status_code, 400, params)

    def test_month_is_isolated_per_user(self):
        other = get_user_model().objects.create_user("other", password="Str0ng!Pass#9")
        Task.objects.create(owner=other, title="Secret", due_date=TODAY)
        with patch(PATCH_TODAY, return_value=TODAY):
            body = self.client.get(reverse("api_month"), {"year": 2026, "month": 10}).content.decode()
        self.assertNotIn("Secret", body)

    # ---- settings / modules ----
    def test_settings_get_creates_row_with_defaults(self):
        data = self.client.get(reverse("api_settings")).json()["settings"]
        self.assertEqual(data["enabled_modules"], [])
        self.assertEqual(data["defaults"]["kind"], "assignment")
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

    def test_settings_unknown_module_is_400(self):
        response = post_json(self.client, reverse("api_settings"), {"enabled_modules": ["nope"]}, "patch")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown module: nope", response.json()["error"]["message"])

    def test_settings_rejects_unknown_fields_and_bad_types(self):
        url = reverse("api_settings")
        self.assertEqual(post_json(self.client, url, {"hack": 1}, "patch").status_code, 400)
        self.assertEqual(post_json(self.client, url, {"enabled_modules": "habits"}, "patch").status_code, 400)
        self.assertEqual(post_json(self.client, url, {"onboarding_done": "yes"}, "patch").status_code, 400)

    def test_registered_module_appears_on_today_and_obeys_exam_mode(self):
        class FakeModule(modules.Module):
            key = "fake"
            title = "Fake"
            description = "test"

            def today_card(self, user, today):
                return {"hello": "world"}

        modules.register(FakeModule)
        try:
            self.assertEqual(self.client.get(reverse("api_modules")).json()["modules"][0]["enabled"], False)
            response = post_json(self.client, reverse("api_settings"), {"enabled_modules": ["fake", "fake"]}, "patch")
            self.assertEqual(response.json()["settings"]["enabled_modules"], ["fake"])

            with patch(PATCH_TODAY, return_value=TODAY):
                today = self.client.get(reverse("api_today")).json()
                exam = self.client.get(reverse("api_today"), {"exam_mode": 1}).json()
            self.assertEqual(today["modules"][0]["card"], {"hello": "world"})
            self.assertEqual(exam["modules"], [])  # keep_in_exam_mode = False

            self.client.patch(reverse("api_settings"), data=json.dumps({"enabled_modules": []}), content_type="application/json")
            with patch(PATCH_TODAY, return_value=TODAY):
                self.assertEqual(self.client.get(reverse("api_today")).json()["modules"], [])
        finally:
            modules.MODULE_REGISTRY.pop("fake", None)

    def test_today_has_no_modules_by_default(self):
        with patch(PATCH_TODAY, return_value=TODAY):
            self.assertEqual(self.client.get(reverse("api_today")).json()["modules"], [])

    # ---- defaults ----
    def test_last_used_defaults_are_remembered(self):
        response = post_json(self.client, reverse("api_tasks"), {
            "title": "Read", "area": "academic", "kind": "study", "priority": "urgent",
            "subject_id": self.subject.id, "due_date": "2026-10-20"})
        self.assertEqual(response.status_code, 201, response.content)
        defaults = self.client.get(reverse("api_task_options")).json()["defaults"]
        self.assertEqual(defaults, {"area": "academic", "kind": "study", "priority": "urgent", "subject_id": self.subject.id})

    def test_deleting_remembered_subject_clears_default(self):
        post_json(self.client, reverse("api_tasks"), {"title": "x", "subject_id": self.subject.id})
        self.subject.delete()
        self.assertIsNone(self.client.get(reverse("api_task_options")).json()["defaults"]["subject_id"])

    # ---- review tasks ----
    def test_exam_with_review_offsets_creates_study_tasks(self):
        with patch(PATCH_TODAY, return_value=TODAY):
            response = post_json(self.client, reverse("api_tasks"), {
                "title": "Midterm", "kind": "exam", "due_date": "2026-10-16",
                "subject_id": self.subject.id, "review_offsets": [7, 3, 1]})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["review_tasks_created"], 3)
        reviews = Task.objects.filter(title="Review: Midterm").order_by("due_date")
        self.assertEqual([t.due_date.isoformat() for t in reviews], ["2026-10-09", "2026-10-13", "2026-10-15"])
        self.assertTrue(all(t.kind == "study" and t.subject_id == self.subject.id for t in reviews))

    def test_review_offsets_ignored_for_non_exam_and_validated(self):
        with patch(PATCH_TODAY, return_value=TODAY):
            ok = post_json(self.client, reverse("api_tasks"), {"title": "HW", "kind": "assignment",
                                                               "due_date": "2026-10-16", "review_offsets": [3]})
            bad = post_json(self.client, reverse("api_tasks"), {"title": "E", "kind": "exam",
                                                                "due_date": "2026-10-16", "review_offsets": [99]})
        self.assertEqual(ok.json()["review_tasks_created"], 0)
        self.assertEqual(bad.status_code, 400)
        self.assertFalse(Task.objects.filter(title="E").exists())

    # ---- subject template ----
    def test_subject_template_creates_assessments_totalling_100(self):
        response = post_json(self.client, reverse("api_subjects"), {
            "name": "Python", "semester": "1/2026", "with_default_assessments": True})
        self.assertEqual(response.status_code, 201, response.content)
        subject = Subject.objects.get(name="Python")
        rows = Assessment.objects.filter(subject=subject)
        self.assertEqual(rows.count(), 4)
        self.assertEqual(sum(a.weight for a in rows), 100)
        self.assertTrue(all(a.score is None for a in rows))

    def test_subject_without_template_has_no_assessments(self):
        post_json(self.client, reverse("api_subjects"), {"name": "Plain"})
        self.assertEqual(Assessment.objects.filter(subject__name="Plain").count(), 0)

    # ---- duplicate ----
    def test_duplicate_copies_task_with_today_and_not_completed(self):
        original = self.task("Report", 10, completed=True, subject=self.subject)
        with patch(PATCH_TODAY, return_value=TODAY):
            response = self.client.post(reverse("api_task_duplicate", args=[original.id]))
        self.assertEqual(response.status_code, 201, response.content)
        copy = Task.objects.exclude(pk=original.pk).get(title="Report")
        self.assertFalse(copy.completed)
        self.assertEqual(copy.due_date, TODAY)
        self.assertEqual(copy.subject_id, self.subject.id)
        self.assertEqual(copy.owner_id, self.user.id)

    def test_duplicate_other_users_task_is_404(self):
        other = get_user_model().objects.create_user("o2", password="Str0ng!Pass#9")
        theirs = Task.objects.create(owner=other, title="Theirs")
        self.assertEqual(self.client.post(reverse("api_task_duplicate", args=[theirs.id])).status_code, 404)

    # ---- suggest exam mode ----
    def test_today_suggests_exam_mode_only_when_off(self):
        self.task("Exam", 5, kind="exam")
        with patch(PATCH_TODAY, return_value=TODAY):
            off = self.client.get(reverse("api_today")).json()
            on = self.client.get(reverse("api_today"), {"exam_mode": 1}).json()
        self.assertTrue(off["suggest_exam_mode"])
        self.assertFalse(on["suggest_exam_mode"])


class FunctionalHelperTests(TestCase):
    def test_status_counts_uses_reduce_and_handles_empty(self):
        from planner.services import status_counts, to_domain_items
        from types import SimpleNamespace

        self.assertEqual(status_counts([], TODAY), {})
        tasks = [
            SimpleNamespace(id=1, title="a", area="academic", kind="general", priority="normal",
                            due_date=TODAY - timedelta(days=1), completed=False),
            SimpleNamespace(id=2, title="b", area="academic", kind="general", priority="normal",
                            due_date=TODAY, completed=False),
            SimpleNamespace(id=3, title="c", area="academic", kind="general", priority="normal",
                            due_date=TODAY, completed=True),
            SimpleNamespace(id=4, title="d", area="academic", kind="exam", priority="normal",
                            due_date=TODAY - timedelta(days=2), completed=False),
        ]
        items = to_domain_items(tasks)
        self.assertEqual(len(items), 4)
        self.assertEqual(
            status_counts(items, TODAY),
            {"overdue": 1, "today": 1, "completed": 1, "past_exam": 1},
        )

    def test_parse_due_date_else_branch_and_error(self):
        from planner.validators import PlanitValidationError, parse_due_date

        self.assertEqual(parse_due_date("2026-10-06"), date(2026, 10, 6))
        with self.assertRaises(PlanitValidationError):
            parse_due_date("06/10/2026")
