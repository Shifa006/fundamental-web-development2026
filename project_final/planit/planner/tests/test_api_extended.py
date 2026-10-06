import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from planner.models import Assessment, Project, Subject, Task


TODAY = date(2026, 10, 6)


class ExtendedApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="extended-user",
            password="TestPass123!",
        )
        self.client.force_login(self.user)

        self.subject = Subject.objects.create(
            owner=self.user,
            name="Web Development",
            code="WEB101",
            semester="1/2026",
            color="butter",
        )
        self.other_subject = Subject.objects.create(
            owner=self.user,
            name="Python Programming",
            code="PY101",
            semester="1/2026",
            color="lavender",
        )

    def json_post(self, name, payload, args=None):
        return self.client.post(
            reverse(name, args=args or []),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def json_patch(self, name, payload, args=None):
        return self.client.patch(
            reverse(name, args=args or []),
            data=json.dumps(payload),
            content_type="application/json",
        )

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_subject_create_read_update_delete(self, mock_localdate):
        create = self.json_post(
            "api_subjects",
            {
                "name": "Cosmetic Science",
                "code": "COS201",
                "semester": "1/2026",
                "color": "sage",
            },
        )
        self.assertEqual(create.status_code, 201)
        subject_id = create.json()["subject"]["id"]

        detail = self.client.get(reverse("api_subject_detail", args=[subject_id]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["subject"]["code"], "COS201")

        update = self.json_patch(
            "api_subject_detail",
            {"code": "COS202"},
            args=[subject_id],
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["subject"]["code"], "COS202")

        delete = self.client.delete(reverse("api_subject_detail", args=[subject_id]))
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Subject.objects.filter(pk=subject_id).exists())

    def test_duplicate_subject_is_rejected(self):
        response = self.json_post(
            "api_subjects",
            {
                "name": self.subject.name,
                "semester": self.subject.semester,
                "code": "OTHER",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "model_validation_error")

    def test_assessment_crud_and_total_weight_validation(self):
        create = self.json_post(
            "api_assessments",
            {
                "subject_id": self.subject.id,
                "name": "Midterm",
                "weight": 40,
                "max_score": 50,
                "score": 45,
            },
        )
        self.assertEqual(create.status_code, 201)
        assessment_id = create.json()["assessment"]["id"]

        update = self.json_patch(
            "api_assessment_detail",
            {"score": 40},
            args=[assessment_id],
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["assessment"]["score"], 40.0)

        Assessment.objects.create(
            subject=self.subject,
            name="Project",
            weight=Decimal("50"),
            max_score=Decimal("100"),
        )

        too_much = self.json_post(
            "api_assessments",
            {
                "subject_id": self.subject.id,
                "name": "Final",
                "weight": 20,
                "max_score": 100,
            },
        )
        self.assertEqual(too_much.status_code, 400)
        self.assertEqual(too_much.json()["error"]["code"], "weight_exceeded")

        delete = self.client.delete(
            reverse("api_assessment_detail", args=[assessment_id])
        )
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Assessment.objects.filter(pk=assessment_id).exists())

    def test_assessment_score_above_max_is_rejected(self):
        response = self.json_post(
            "api_assessments",
            {
                "subject_id": self.subject.id,
                "name": "Quiz",
                "weight": 10,
                "max_score": 20,
                "score": 21,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["field"], "score")

    @patch("planner.views.timezone.localdate", return_value=TODAY)
    def test_project_create_update_delete_and_progress(self, mock_localdate):
        create = self.json_post(
            "api_projects",
            {
                "title": "Portfolio",
                "subject_id": self.subject.id,
                "due_date": (TODAY + timedelta(days=20)).isoformat(),
            },
        )
        self.assertEqual(create.status_code, 201)
        project_id = create.json()["project"]["id"]

        Task.objects.create(
            owner=self.user,
            title="Done item",
            area="academic",
            kind="general",
            completed=True,
            subject=self.subject,
            project_id=project_id,
            due_date=TODAY,
        )
        Task.objects.create(
            owner=self.user,
            title="Open item",
            area="academic",
            kind="general",
            completed=False,
            subject=self.subject,
            project_id=project_id,
            due_date=TODAY,
        )

        detail = self.client.get(reverse("api_project_detail", args=[project_id]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["project"]["progress"]["percent"], 50.0)

        update = self.json_patch(
            "api_project_detail",
            {"title": "Portfolio Final"},
            args=[project_id],
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["project"]["title"], "Portfolio Final")

        delete = self.client.delete(reverse("api_project_detail", args=[project_id]))
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Project.objects.filter(pk=project_id).exists())
        self.assertEqual(Task.objects.filter(project__isnull=True).count(), 2)

    def test_project_subject_conflict_is_rejected(self):
        project = Project.objects.create(
            owner=self.user,
            title="Mixed project",
            subject=self.subject,
        )
        Task.objects.create(
            owner=self.user,
            title="Web task",
            area="academic",
            kind="general",
            subject=self.subject,
            project=project,
        )

        response = self.json_patch(
            "api_project_detail",
            {"subject_id": self.other_subject.id},
            args=[project.id],
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "project_subject_conflict")

    def test_missing_resources_return_404(self):
        cases = [
            ("api_task_detail", [999999]),
            ("api_subject_detail", [999999]),
            ("api_assessment_detail", [999999]),
            ("api_project_detail", [999999]),
        ]

        for name, args in cases:
            with self.subTest(name=name):
                response = self.client.patch(
                    reverse(name, args=args),
                    data=json.dumps({}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 404)

    def test_wrong_methods_return_405_with_allow_header(self):
        response = self.client.post(reverse("api_today"), data={})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "GET")

        response = self.client.get(reverse("api_assessments"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "POST")
