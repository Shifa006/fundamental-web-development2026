from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from planner.models import Assessment, Project, Subject, Task


class ModelValidationTests(TestCase):
    def setUp(self):
        self.subject_a = Subject.objects.create(
            name="Web Development",
            code="WEB101",
            semester="1/2026",
        )
        self.subject_b = Subject.objects.create(
            name="Python Programming",
            code="PY101",
            semester="1/2026",
        )
        self.project = Project.objects.create(
            title="Planit",
            subject=self.subject_a,
        )

    def test_personal_task_rules_are_enforced_by_model_validation(self):
        task = Task(
            title="Invalid personal exam",
            area="personal",
            kind="exam",
            subject=self.subject_a,
        )

        with self.assertRaises(ValidationError) as context:
            task.full_clean()

        errors = context.exception.message_dict
        self.assertIn("kind", errors)
        self.assertIn("subject", errors)
        self.assertIn("due_date", errors)

    def test_exam_requires_due_date_at_model_level(self):
        task = Task(
            title="Final exam",
            area="academic",
            kind="exam",
        )

        with self.assertRaises(ValidationError) as context:
            task.full_clean()

        self.assertIn("due_date", context.exception.message_dict)

    def test_project_subject_is_inherited_during_model_validation(self):
        task = Task(
            title="Project task",
            area="academic",
            kind="general",
            project=self.project,
        )

        task.full_clean()
        self.assertEqual(task.subject_id, self.subject_a.id)

    def test_project_subject_mismatch_is_rejected(self):
        task = Task(
            title="Mismatched task",
            area="academic",
            kind="general",
            subject=self.subject_b,
            project=self.project,
        )

        with self.assertRaises(ValidationError) as context:
            task.full_clean()

        self.assertIn("subject", context.exception.message_dict)

    def test_database_constraint_blocks_invalid_personal_task(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Task.objects.create(
                    title="Direct ORM invalid task",
                    area="personal",
                    kind="study",
                )

    def test_database_constraint_blocks_exam_without_date(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Task.objects.create(
                    title="Direct ORM exam",
                    area="academic",
                    kind="exam",
                )

    def test_assessment_score_cannot_exceed_max_score(self):
        assessment = Assessment(
            subject=self.subject_a,
            name="Midterm",
            weight=Decimal("30"),
            max_score=Decimal("20"),
            score=Decimal("21"),
        )

        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()

        self.assertIn("score", context.exception.message_dict)

    def test_assessment_total_weight_cannot_exceed_100(self):
        Assessment.objects.create(
            subject=self.subject_a,
            name="Existing",
            weight=Decimal("80"),
            max_score=Decimal("100"),
        )
        assessment = Assessment(
            subject=self.subject_a,
            name="Too much",
            weight=Decimal("30"),
            max_score=Decimal("100"),
        )

        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()

        self.assertIn("weight", context.exception.message_dict)

    def test_database_constraint_blocks_invalid_assessment_score(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Assessment.objects.create(
                    subject=self.subject_a,
                    name="Broken",
                    weight=Decimal("10"),
                    max_score=Decimal("10"),
                    score=Decimal("11"),
                )

    def test_project_model_rejects_subject_change_with_conflicting_tasks(self):
        task = Task.objects.create(
            title="Linked task",
            area="academic",
            kind="general",
            subject=self.subject_b,
            project=self.project,
            due_date=date(2026, 10, 7),
        )
        self.assertEqual(task.project_id, self.project.id)

        self.project.subject = self.subject_a
        with self.assertRaises(ValidationError) as context:
            self.project.full_clean()

        self.assertIn("subject", context.exception.message_dict)
