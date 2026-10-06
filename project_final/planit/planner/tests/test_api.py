from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from planner.models import (
    Project,
    Subject,
    Task,
)


TODAY = date(
    2026,
    10,
    6,
)


class ApiTests(TestCase):

    def setUp(self):
        self.subject = (
            Subject.objects.create(
                name="Web Development",
                code="WEB101",
                semester="1/2026",
                color="butter",
            )
        )

        self.project = (
            Project.objects.create(
                title="Planit Final Project",
                subject=self.subject,
                due_date=(
                    TODAY
                    + timedelta(days=24)
                ),
            )
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
        due_date = (
            None
            if days is None
            else TODAY
            + timedelta(days=days)
        )

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

    @patch(
        "planner.views.timezone.localdate",
        return_value=TODAY,
    )
    def test_tasks_api(
        self,
        mock_localdate,
    ):
        self.create_task(
            "Submit Web Final",
            priority="urgent",
            days=4,
            subject=self.subject,
            project=self.project,
        )

        response = self.client.get(
            reverse("api_tasks")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["meta"]["today"],
            "2026-10-06",
        )

        self.assertEqual(
            len(data["tasks"]),
            1,
        )

        task = data["tasks"][0]

        self.assertEqual(
            task["title"],
            "Submit Web Final",
        )

        self.assertEqual(
            task["status"],
            "upcoming",
        )

        self.assertEqual(
            task["days_left"],
            4,
        )

        self.assertEqual(
            task["subject"]["name"],
            "Web Development",
        )

        self.assertEqual(
            task["project"]["title"],
            "Planit Final Project",
        )

    @patch(
        "planner.views.timezone.localdate",
        return_value=TODAY,
    )
    def test_today_api(
        self,
        mock_localdate,
    ):
        self.create_task(
            "Math homework",
            days=0,
        )

        self.create_task(
            "Review notes",
            days=0,
            completed=True,
        )

        self.create_task(
            "Late report",
            priority="urgent",
            days=-1,
        )

        exam = self.create_task(
            "Calculus Exam",
            kind="exam",
            priority="urgent",
            days=3,
        )

        response = self.client.get(
            reverse("api_today")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["progress"],
            {
                "completed": 1,
                "total": 2,
                "percent": 50.0,
            },
        )

        self.assertEqual(
            len(data["today"]),
            2,
        )

        self.assertEqual(
            len(data["overdue"]),
            1,
        )

        self.assertEqual(
            data["next_exam"]["id"],
            exam.id,
        )

    def test_invalid_area_returns_400(
        self,
    ):
        response = self.client.get(
            reverse("api_today"),
            {
                "area": "school",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        data = response.json()

        self.assertEqual(
            data["error"]["code"],
            "invalid_query_parameter",
        )

    def test_invalid_exam_mode_returns_400(
        self,
    ):
        response = self.client.get(
            reverse("api_today"),
            {
                "exam_mode": "yes",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_post_to_get_endpoint_returns_405(
        self,
    ):
        response = self.client.post(
            reverse("api_today"),
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        data = response.json()

        self.assertEqual(
            data["error"]["code"],
            "method_not_allowed",
        )

    @patch(
        "planner.views.timezone.localdate",
        return_value=TODAY,
    )
    def test_week_has_seven_days(
        self,
        mock_localdate,
    ):
        response = self.client.get(
            reverse("api_week")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            len(data["days"]),
            7,
        )

        self.assertEqual(
            data["meta"]["week_start"],
            "2026-10-05",
        )

        self.assertEqual(
            data["meta"]["week_end"],
            "2026-10-11",
        )

    @patch(
        "planner.views.timezone.localdate",
        return_value=TODAY,
    )
    def test_past_exam_stays_in_week_exam_mode(
        self,
        mock_localdate,
    ):
        past_exam = self.create_task(
            "Monday Exam",
            kind="exam",
            days=-1,
        )

        response = self.client.get(
            reverse("api_week"),
            {
                "exam_mode": "1",
            },
        )

        data = response.json()

        monday = data["days"][0]

        task_ids = [
            task["id"]
            for task
            in monday["tasks"]
        ]

        self.assertIn(
            past_exam.id,
            task_ids,
        )

        self.assertEqual(
            monday["tasks"][0]["status"],
            "past_exam",
        )

    def test_page_sets_csrf_cookie(
        self,
    ):
        response = self.client.get(
            reverse("today")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "csrftoken",
            response.cookies,
        )