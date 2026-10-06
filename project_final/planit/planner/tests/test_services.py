from datetime import date, timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase

from planner.domain import ExamItem, GeneralItem, PersonalItem
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
    top_focus_item,
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
        due_date = None if days is None else TODAY + timedelta(days=days)
        return item_class(
            id=id,
            title=f"Task {id}",
            area=area,
            kind=kind,
            priority=priority,
            due_date=due_date,
            completed=completed,
        )

    def test_domain_factory(self):
        task = SimpleNamespace(
            id=10,
            title="Exam",
            area="academic",
            kind="exam",
            priority="urgent",
            due_date=TODAY,
            completed=False,
        )
        self.assertIsInstance(to_domain_item(task), ExamItem)

    def test_higher_order_filters(self):
        items = [
            self.make_item(id=1, area="academic", days=-1),
            self.make_item(id=2, area="academic", days=4),
            self.make_item(id=3, item_class=PersonalItem, area="personal", days=-1),
        ]

        predicate = compose(
            by_area("academic"),
            by_status(TODAY, "overdue"),
        )

        result = select(items, predicate)
        self.assertEqual([item.id for item in result], [1])

    def test_completion_excludes_past_exam(self):
        items = [
            self.make_item(id=1, completed=True),
            self.make_item(id=2, completed=False),
            self.make_item(id=3, item_class=ExamItem, kind="exam", days=-2),
        ]
        self.assertEqual(
            completion_rate(items, TODAY),
            {"completed": 1, "total": 2, "percent": 50.0},
        )

    def test_empty_project_progress(self):
        self.assertEqual(
            project_progress([], TODAY),
            {"completed": 0, "total": 0, "percent": None},
        )

    def test_nearest_exam(self):
        items = [
            self.make_item(id=1, item_class=ExamItem, kind="exam", days=10),
            self.make_item(id=2, item_class=ExamItem, kind="exam", days=3),
            self.make_item(id=3, days=1),
        ]
        self.assertEqual(nearest_exam(items, TODAY).id, 2)

    def test_overdue_priority_beats_age(self):
        urgent = self.make_item(id=1, priority="urgent", days=-2)
        later = self.make_item(id=2, priority="later", days=-30)
        result = sort_by_attention([later, urgent], TODAY)
        self.assertEqual(result[0].id, 1)


    def test_top_focus_returns_highest_ranked_active_item(self):
        items = [
            self.make_item(id=1, priority="normal", days=2),
            self.make_item(id=2, priority="urgent", days=-1),
            self.make_item(id=3, completed=True, days=0),
        ]

        self.assertEqual(top_focus_item(items, TODAY).id, 2)

    def test_today_payload(self):
        items = [
            self.make_item(id=1, days=0),
            self.make_item(id=2, days=0, completed=True),
            self.make_item(id=3, priority="urgent", days=-1),
            self.make_item(id=4, item_class=ExamItem, kind="exam", days=3),
        ]
        result = build_today_payload(items, TODAY)

        self.assertEqual(
            result["progress"],
            {"completed": 1, "total": 2, "percent": 50.0},
        )
        self.assertEqual(len(result["overdue"]), 1)
        self.assertEqual(len(result["today"]), 2)
        self.assertEqual(result["next_exam"].id, 4)

    def test_exam_mode_hidden_count_includes_future_active_items(self):
        items = [
            self.make_item(id=1, priority="normal", days=10),
            self.make_item(id=2, priority="urgent", days=2),
            self.make_item(id=3, priority="later", days=0),
            self.make_item(id=4, completed=True, days=10),
        ]

        result = build_today_payload(items, TODAY, exam_mode=True)

        # Normal +10 days and Later due today are active but hidden by Exam Mode.
        # The completed task is not counted.
        self.assertEqual(result["hidden_by_exam_mode"], 2)

    def test_project_progress_counts_unfinished_past_exam(self):
        items = [
            self.make_item(id=1, completed=True),
            self.make_item(id=2, item_class=ExamItem, kind="exam", days=-2),
        ]

        self.assertEqual(
            project_progress(items, TODAY),
            {"completed": 1, "total": 2, "percent": 50.0},
        )
