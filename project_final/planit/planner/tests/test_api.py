import json
from datetime import date, timedelta
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from planner.models import Assessment, Project, Subject, Task


TODAY = date(2026, 10, 6)


class ApiTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(
            name="Web Development",
            code="WEB101",
            semester="1/2026",
            color="butter",
        )
        self.project = Project.objects.create(
            title="Planit Final Project",
            subject=self.subject,
            due_date=TODAY + timedelta(days=24),
        )

    def create_task(
        self,
        title,
        *,
        area="academic",
        kind="general",
        priority="normal",
        days=0,
        completed=False,
        subject=None,
        project=None,
    ):
        due_date = None if days is None else TODAY + timedelta(days=days)
        return Task.objects.create(
            title=title,
            area=area,
            kind=kind,
            priority=priority,
            due_date=due_date,
            completed=completed,
            subject=subject,
            project=project,
        )

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_tasks_api_serializes_domain_fields(self, mock_localdate):
        self.create_task(
            "Submit Web Final",
            priority="urgent",
            days=4,
            subject=self.subject,
            project=self.project,
        )
        response = self.client.get(reverse("api_tasks"))
        self.assertEqual(response.status_code, 200)
        task = response.json()["tasks"][0]
        self.assertEqual(task["status"], "upcoming")
        self.assertEqual(task["days_left"], 4)
        self.assertEqual(task["subject"]["name"], "Web Development")

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_today_api(self, mock_localdate):
        self.create_task("Math homework", days=0)
        self.create_task("Review notes", days=0, completed=True)
        self.create_task("Late report", priority="urgent", days=-1)
        exam = self.create_task("Calculus Exam", kind="exam", priority="urgent", days=3)

        response = self.client.get(reverse("api_today"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            data["progress"],
            {"completed": 1, "total": 2, "percent": 50.0},
        )
        self.assertEqual(len(data["overdue"]), 1)
        self.assertEqual(data["next_exam"]["id"], exam.id)

    def test_invalid_query_returns_400(self):
        response = self.client.get(reverse("api_today"), {"area": "school"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_query_parameter")

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_week_keeps_past_exam_in_exam_mode(self, mock_localdate):
        past_exam = self.create_task("Monday Exam", kind="exam", days=-1)
        response = self.client.get(reverse("api_week"), {"exam_mode": "1"})
        monday = response.json()["days"][0]
        self.assertIn(past_exam.id, [task["id"] for task in monday["tasks"]])
        self.assertEqual(monday["tasks"][0]["status"], "past_exam")

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_create_patch_delete_task(self, mock_localdate):
        create_response = self.client.post(
            reverse("api_tasks"),
            data=json.dumps(
                {
                    "title": "Prepare presentation",
                    "area": "academic",
                    "kind": "study",
                    "priority": "urgent",
                    "due_date": "2026-10-06",
                    "subject_id": self.subject.id,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["task"]["id"]

        patch_response = self.client.patch(
            reverse("api_task_detail", args=[task_id]),
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertTrue(Task.objects.get(pk=task_id).completed)

        delete_response = self.client.delete(reverse("api_task_detail", args=[task_id]))
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_project_autofills_subject(self, mock_localdate):
        response = self.client.post(
            reverse("api_tasks"),
            data=json.dumps(
                {
                    "title": "Project task",
                    "project_id": self.project.id,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Task.objects.get(title="Project task").subject_id,
            self.subject.id,
        )

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            reverse("api_tasks"),
            data="{bad json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_json")

    def test_personal_exam_rejected(self):
        response = self.client.post(
            reverse("api_tasks"),
            data=json.dumps(
                {
                    "title": "Personal exam",
                    "area": "personal",
                    "kind": "exam",
                    "due_date": "2026-10-10",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("api_tasks"),
            data=json.dumps({"title": "Blocked task"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_course_grade_canonical_case(self, mock_localdate):
        Assessment.objects.create(
            subject=self.subject,
            name="Assignment",
            weight=20,
            max_score=20,
            score=18,
        )
        Assessment.objects.create(
            subject=self.subject,
            name="Midterm",
            weight=30,
            max_score=30,
            score=24,
        )
        Assessment.objects.create(
            subject=self.subject,
            name="Project",
            weight=20,
            max_score=20,
            score=None,
        )
        Assessment.objects.create(
            subject=self.subject,
            name="Final",
            weight=30,
            max_score=30,
            score=None,
        )

        response = self.client.get(
            reverse("api_subject_grade", args=[self.subject.id]),
            {"target": "80"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["grade"]["required"], 76.0)

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_project_progress_is_derived(self, mock_localdate):
        self.create_task(
            "Project one",
            completed=True,
            project=self.project,
            subject=self.subject,
        )
        self.create_task(
            "Project two",
            completed=False,
            project=self.project,
            subject=self.subject,
        )

        response = self.client.get(reverse("api_project_detail", args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["project"]["progress"]["percent"], 50.0)

    def test_page_sets_csrf_cookie(self):
        response = self.client.get(reverse("today"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
