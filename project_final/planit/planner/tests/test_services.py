from datetime import date, timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase

from planner.domain import (
    ExamItem,
    GeneralItem,
    PersonalItem,
)
from planner.services import (
    build_today_payload,
    by_area,
    by_status,
    completion_rate,
    compose,
    nearest_exam,
    project_progress,
    select,
    sort_by_attention,
    to_domain_item,
)


TODAY = date(2026, 10, 6)


class ServiceTests(SimpleTestCase):

    def make_item(
        self,
        *,
        id=1,
        item_class=GeneralItem,
        area="academic",
        kind="general",
        priority="normal",
        days=0,
        completed=False,
    ):
        due_date = (
            None
            if days is None
            else TODAY + timedelta(
                days=days
            )
        )

        return item_class(
            id=id,
            title=f"Task {id}",
            area=area,
            kind=kind,
            priority=priority,
            due_date=due_date,
            completed=completed,
        )

    def test_to_domain_item(self):
        task = SimpleNamespace(
            id=10,
            title="Exam",
            area="academic",
            kind="exam",
            priority="urgent",
            due_date=TODAY,
            completed=False,
        )

        item = to_domain_item(
            task
        )

        self.assertIsInstance(
            item,
            ExamItem,
        )

    def test_invalid_domain_combination(self):
        task = SimpleNamespace(
            id=10,
            title="Invalid",
            area="personal",
            kind="exam",
            priority="urgent",
            due_date=TODAY,
            completed=False,
        )

        with self.assertRaises(
            ValueError
        ):
            to_domain_item(
                task
            )

    def test_higher_order_filters(self):
        items = [
            self.make_item(
                id=1,
                area="academic",
                days=-1,
            ),
            self.make_item(
                id=2,
                area="academic",
                days=4,
            ),
            self.make_item(
                id=3,
                item_class=PersonalItem,
                area="personal",
                days=-1,
            ),
        ]

        predicate = compose(
            by_area(
                "academic"
            ),
            by_status(
                TODAY,
                "overdue",
            ),
        )

        result = select(
            items,
            predicate,
        )

        self.assertEqual(
            [item.id for item in result],
            [1],
        )

    def test_completion_rate_excludes_past_exam(self):
        items = [
            self.make_item(
                id=1,
                completed=True,
            ),
            self.make_item(
                id=2,
                completed=False,
            ),
            self.make_item(
                id=3,
                item_class=ExamItem,
                kind="exam",
                days=-2,
            ),
        ]

        result = completion_rate(
            items,
            TODAY,
        )

        self.assertEqual(
            result,
            {
                "completed": 1,
                "total": 2,
                "percent": 50.0,
            },
        )

    def test_empty_progress_has_no_percent(self):
        result = project_progress(
            [],
            TODAY,
        )

        self.assertEqual(
            result["completed"],
            0,
        )

        self.assertEqual(
            result["total"],
            0,
        )

        self.assertIsNone(
            result["percent"]
        )

    def test_nearest_exam(self):
        items = [
            self.make_item(
                id=1,
                item_class=ExamItem,
                kind="exam",
                days=10,
            ),
            self.make_item(
                id=2,
                item_class=ExamItem,
                kind="exam",
                days=3,
            ),
            self.make_item(
                id=3,
                days=1,
            ),
        ]

        result = nearest_exam(
            items,
            TODAY,
        )

        self.assertEqual(
            result.id,
            2,
        )

    def test_past_exam_is_not_next_exam(self):
        items = [
            self.make_item(
                id=1,
                item_class=ExamItem,
                kind="exam",
                days=-2,
            )
        ]

        self.assertIsNone(
            nearest_exam(
                items,
                TODAY,
            )
        )

    def test_overdue_priority_beats_age(self):
        urgent = self.make_item(
            id=1,
            priority="urgent",
            days=-2,
        )

        later = self.make_item(
            id=2,
            priority="later",
            days=-30,
        )

        result = sort_by_attention(
            [
                later,
                urgent,
            ],
            TODAY,
        )

        self.assertEqual(
            result[0].id,
            1,
        )

    def test_build_today_payload(self):
        items = [
            self.make_item(
                id=1,
                days=0,
                completed=False,
            ),
            self.make_item(
                id=2,
                days=0,
                completed=True,
            ),
            self.make_item(
                id=3,
                priority="urgent",
                days=-1,
            ),
            self.make_item(
                id=4,
                item_class=ExamItem,
                kind="exam",
                days=3,
            ),
        ]

        result = build_today_payload(
            items,
            TODAY,
        )

        self.assertEqual(
            result["progress"],
            {
                "completed": 1,
                "total": 2,
                "percent": 50.0,
            },
        )

        self.assertEqual(
            len(
                result["overdue"]
            ),
            1,
        )

        self.assertEqual(
            len(
                result["today"]
            ),
            2,
        )

        self.assertEqual(
            result["next_exam"].id,
            4,
        )

    def test_exam_mode_hidden_count(self):
        items = [
            self.make_item(
                id=1,
                item_class=PersonalItem,
                area="personal",
                priority="normal",
                days=0,
            ),
            self.make_item(
                id=2,
                item_class=PersonalItem,
                area="personal",
                priority="urgent",
                days=0,
            ),
            self.make_item(
                id=3,
                completed=True,
                days=0,
            ),
        ]

        result = build_today_payload(
            items,
            TODAY,
            area="all",
            exam_mode=True,
        )

        self.assertEqual(
            result[
                "hidden_by_exam_mode"
            ],
            1,
        )

    def test_personal_area_has_no_next_exam(self):
        items = [
            self.make_item(
                id=1,
                item_class=ExamItem,
                kind="exam",
                days=2,
            ),
            self.make_item(
                id=2,
                item_class=PersonalItem,
                area="personal",
                priority="urgent",
                days=0,
            ),
        ]

        result = build_today_payload(
            items,
            TODAY,
            area="personal",
        )

        self.assertIsNone(
            result["next_exam"]
        )