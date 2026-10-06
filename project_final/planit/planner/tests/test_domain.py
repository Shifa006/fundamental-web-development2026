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
        due_date = (
            None
            if days is None
            else TODAY + timedelta(days=days)
        )

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
            (
                self.make_item(completed=True),
                "completed",
            ),
            (
                self.make_item(
                    ExamItem,
                    kind="exam",
                    days=-1,
                ),
                "past_exam",
            ),
            (
                self.make_item(days=None),
                "no_date",
            ),
            (
                self.make_item(days=-1),
                "overdue",
            ),
            (
                self.make_item(days=0),
                "today",
            ),
            (
                self.make_item(days=5),
                "upcoming",
            ),
        ]

        for item, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    item.status(TODAY),
                    expected,
                )

    def test_days_left_without_date(self):
        item = self.make_item(
            days=None
        )

        self.assertIsNone(
            item.days_left(TODAY)
        )

    def test_days_overdue(self):
        item = self.make_item(
            days=-4
        )

        self.assertEqual(
            item.days_overdue(TODAY),
            4,
        )

    def test_general_exam_mode_boundaries(self):
        cases = [
            ("urgent", 7, True),
            ("urgent", 8, False),
            ("urgent", None, True),
            ("normal", 3, True),
            ("normal", 4, False),
            ("normal", None, False),
            ("later", -1, True),
            ("later", 0, False),
        ]

        for priority, days, expected in cases:
            with self.subTest(
                priority=priority,
                days=days,
            ):
                item = self.make_item(
                    priority=priority,
                    days=days,
                )

                self.assertEqual(
                    item.visible_in_exam_mode(
                        TODAY
                    ),
                    expected,
                )

    def test_study_exam_mode(self):
        cases = [
            ("urgent", None, True),
            ("urgent", 3, True),
            ("urgent", 4, False),
            ("normal", 3, True),
            ("normal", 4, False),
            ("later", -1, True),
            ("later", 0, False),
        ]

        for priority, days, expected in cases:
            with self.subTest(
                priority=priority,
                days=days,
            ):
                item = self.make_item(
                    StudyItem,
                    kind="study",
                    priority=priority,
                    days=days,
                )

                self.assertEqual(
                    item.visible_in_exam_mode(
                        TODAY
                    ),
                    expected,
                )

    def test_exam_mode_exam_window(self):
        cases = [
            (0, True),
            (14, True),
            (15, False),
            (-1, False),
        ]

        for days, expected in cases:
            with self.subTest(days=days):
                item = self.make_item(
                    ExamItem,
                    kind="exam",
                    days=days,
                )

                self.assertEqual(
                    item.visible_in_exam_mode(
                        TODAY
                    ),
                    expected,
                )

    def test_personal_exam_mode(self):
        cases = [
            ("urgent", None, True),
            ("urgent", 7, True),
            ("urgent", 8, False),
            ("urgent", -1, True),
            ("normal", 0, False),
            ("normal", -1, False),
        ]

        for priority, days, expected in cases:
            with self.subTest(
                priority=priority,
                days=days,
            ):
                item = self.make_item(
                    PersonalItem,
                    area="personal",
                    kind="general",
                    priority=priority,
                    days=days,
                )

                self.assertEqual(
                    item.visible_in_exam_mode(
                        TODAY
                    ),
                    expected,
                )

    def test_completed_item_hidden_in_exam_mode(self):
        item = self.make_item(
            priority="urgent",
            completed=True,
        )

        self.assertFalse(
            item.visible_in_exam_mode(
                TODAY
            )
        )

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

        self.assertEqual(
            assignment.attention_score(
                TODAY
            ),
            Decimal("0.6"),
        )

        self.assertEqual(
            exam.attention_score(
                TODAY
            ),
            Decimal("1"),
        )

        self.assertEqual(
            personal.attention_score(
                TODAY
            ),
            Decimal("1.50"),
        )


class GradeComponentTests(SimpleTestCase):

    def test_score_zero_is_valid(self):
        component = GradeComponent(
            "Quiz",
            10,
            20,
            0,
        )

        self.assertEqual(
            component.score,
            Decimal("0"),
        )

    def test_score_cannot_exceed_maximum(self):
        with self.assertRaises(
            ValueError
        ):
            GradeComponent(
                "Quiz",
                10,
                20,
                21,
            )

    def test_maximum_score_must_be_positive(self):
        with self.assertRaises(
            ValueError
        ):
            GradeComponent(
                "Quiz",
                10,
                0,
            )

    def test_weight_cannot_exceed_100(self):
        with self.assertRaises(
            ValueError
        ):
            GradeComponent(
                "Quiz",
                101,
                20,
            )


class GradeBookTests(SimpleTestCase):

    def make_canonical_gradebook(self):
        return GradeBook([
            GradeComponent(
                "Assignment",
                20,
                20,
                18,
            ),
            GradeComponent(
                "Midterm",
                30,
                30,
                24,
            ),
            GradeComponent(
                "Project",
                20,
                20,
            ),
            GradeComponent(
                "Final",
                30,
                30,
            ),
        ])

    def test_canonical_grade_case(self):
        gradebook = (
            self.make_canonical_gradebook()
        )

        result = gradebook.required_average(
            80
        )

        self.assertEqual(
            gradebook.configured_weight,
            Decimal("100"),
        )

        self.assertEqual(
            gradebook.graded_weight,
            Decimal("50"),
        )

        self.assertEqual(
            gradebook.earned_course_points,
            Decimal("42"),
        )

        self.assertEqual(
            gradebook.average_on_graded_work,
            Decimal("84"),
        )

        self.assertEqual(
            result["status"],
            "possible",
        )

        self.assertEqual(
            result["required"],
            Decimal("76"),
        )

    def test_target_already_achieved(self):
        gradebook = (
            self.make_canonical_gradebook()
        )

        result = gradebook.required_average(
            40
        )

        self.assertEqual(
            result["status"],
            "achieved",
        )

    def test_target_exactly_100_required(self):
        gradebook = (
            self.make_canonical_gradebook()
        )

        result = gradebook.required_average(
            92
        )

        self.assertEqual(
            result["status"],
            "possible",
        )

        self.assertEqual(
            result["required"],
            Decimal("100"),
        )

    def test_impossible_target(self):
        gradebook = (
            self.make_canonical_gradebook()
        )

        result = gradebook.required_average(
            95
        )

        self.assertEqual(
            result["status"],
            "impossible",
        )

        self.assertEqual(
            result["required"],
            Decimal("106"),
        )

    def test_incomplete_configuration(self):
        gradebook = GradeBook([
            GradeComponent(
                "Assignment",
                20,
                20,
                18,
            )
        ])

        result = gradebook.required_average(
            80
        )

        self.assertEqual(
            result["status"],
            "incomplete_configuration",
        )

        self.assertIsNone(
            result["required"]
        )

    def test_constructor_validates_total_weight(self):
        with self.assertRaises(
            ValueError
        ):
            GradeBook([
                GradeComponent(
                    "One",
                    60,
                    100,
                ),
                GradeComponent(
                    "Two",
                    60,
                    100,
                ),
            ])