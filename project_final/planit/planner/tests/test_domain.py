from datetime import date, timedelta
from decimal import Decimal

from django.test import SimpleTestCase

from planner.domain import (
    AssignmentItem,
    ExamItem,
    GeneralItem,
    GradeBook,
    GradeComponent,
    PersonalItem,
    StudyItem,
)


TODAY = date(2026, 10, 6)


class PlannerItemTests(SimpleTestCase):
    def make_item(
        self,
        item_class=GeneralItem,
        *,
        id=1,
        area="academic",
        kind="general",
        priority="normal",
        days=0,
        completed=False,
    ):
        due_date = None if days is None else TODAY + timedelta(days=days)
        return item_class(
            id=id,
            title="Test item",
            area=area,
            kind=kind,
            priority=priority,
            due_date=due_date,
            completed=completed,
        )

    def test_statuses(self):
        cases = [
            (self.make_item(completed=True), "completed"),
            (self.make_item(ExamItem, kind="exam", days=-1), "past_exam"),
            (self.make_item(days=None), "no_date"),
            (self.make_item(days=-1), "overdue"),
            (self.make_item(days=0), "today"),
            (self.make_item(days=5), "upcoming"),
        ]

        for item, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(item.status(TODAY), expected)

    def test_exam_mode_boundaries(self):
        cases = [
            (GeneralItem, "general", "urgent", 7, True),
            (GeneralItem, "general", "urgent", 8, False),
            (GeneralItem, "general", "normal", 3, True),
            (GeneralItem, "general", "normal", 4, False),
            (StudyItem, "study", "urgent", None, True),
            (StudyItem, "study", "urgent", 4, False),
            (ExamItem, "exam", "normal", 14, True),
            (ExamItem, "exam", "normal", 15, False),
            (PersonalItem, "general", "urgent", 7, True),
            (PersonalItem, "general", "urgent", 8, False),
        ]

        for item_class, kind, priority, days, expected in cases:
            with self.subTest(item_class=item_class.__name__, days=days):
                item = self.make_item(
                    item_class,
                    area="personal" if item_class is PersonalItem else "academic",
                    kind=kind,
                    priority=priority,
                    days=days,
                )
                self.assertEqual(item.visible_in_exam_mode(TODAY), expected)

    def test_attention_scores(self):
        assignment = self.make_item(
            AssignmentItem,
            kind="assignment",
            priority="urgent",
            days=4,
        )
        exam = self.make_item(
            ExamItem,
            kind="exam",
            priority="normal",
            days=3,
        )
        personal = self.make_item(
            PersonalItem,
            area="personal",
            priority="urgent",
            days=0,
        )

        self.assertEqual(assignment.attention_score(TODAY), Decimal("0.6"))
        self.assertEqual(exam.attention_score(TODAY), Decimal("1"))
        self.assertEqual(personal.attention_score(TODAY), Decimal("1.50"))


class GradeBookTests(SimpleTestCase):
    def make_gradebook(self):
        return GradeBook(
            [
                GradeComponent("Assignment", 20, 20, 18),
                GradeComponent("Midterm", 30, 30, 24),
                GradeComponent("Project", 20, 20),
                GradeComponent("Final", 30, 30),
            ]
        )

    def test_canonical_grade_case(self):
        book = self.make_gradebook()
        result = book.required_average(80)

        self.assertEqual(book.configured_weight, Decimal("100"))
        self.assertEqual(book.graded_weight, Decimal("50"))
        self.assertEqual(book.earned_course_points, Decimal("42"))
        self.assertEqual(book.average_on_graded_work, Decimal("84"))
        self.assertEqual(result["status"], "possible")
        self.assertEqual(result["required"], Decimal("76"))

    def test_score_zero_is_valid(self):
        component = GradeComponent("Quiz", 10, 20, 0)
        self.assertEqual(component.score, Decimal("0"))

    def test_invalid_score_is_rejected(self):
        with self.assertRaises(ValueError):
            GradeComponent("Quiz", 10, 20, 21)

    def test_constructor_validates_total_weight(self):
        with self.assertRaises(ValueError):
            GradeBook(
                [
                    GradeComponent("One", 60, 100),
                    GradeComponent("Two", 60, 100),
                ]
            )
