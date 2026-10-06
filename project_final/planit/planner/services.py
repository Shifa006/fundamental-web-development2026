from decimal import Decimal

from .domain import (
    AssignmentItem,
    ExamItem,
    GeneralItem,
    PersonalItem,
    PRIORITY_RANK,
    StudyItem,
)


ITEM_CLASSES = {
    (
        "academic",
        "general",
    ): GeneralItem,

    (
        "academic",
        "assignment",
    ): AssignmentItem,

    (
        "academic",
        "study",
    ): StudyItem,

    (
        "academic",
        "exam",
    ): ExamItem,

    (
        "personal",
        "general",
    ): PersonalItem,
}


STATUS_BUCKET = {
    "overdue": 1,
    "today": 2,
    "upcoming": 3,
    "no_date": 4,
    "completed": 5,
    "past_exam": 5,
}


def to_domain_item(task):
    key = (
        task.area,
        task.kind,
    )

    item_class = ITEM_CLASSES.get(
        key
    )

    if item_class is None:
        raise ValueError(
            "Invalid task area and kind combination."
        )

    return item_class(
        id=task.id,
        title=task.title,
        area=task.area,
        kind=task.kind,
        priority=task.priority,
        due_date=task.due_date,
        completed=task.completed,
    )


def select(items, predicate):
    return list(
        filter(
            predicate,
            items,
        )
    )


def by_area(area):
    if area not in (
        "all",
        "academic",
        "personal",
    ):
        raise ValueError(
            "Invalid area."
        )

    return lambda item: (
        area == "all"
        or item.area == area
    )


def by_status(
    today,
    *statuses,
):
    allowed = set(
        statuses
    )

    return lambda item: (
        item.status(today)
        in allowed
    )


def compose(*predicates):
    def combined(item):
        return all(
            predicate(item)
            for predicate in predicates
        )

    return combined


def exam_mode_view(
    items,
    today,
):
    return select(
        items,
        lambda item:
            item.visible_in_exam_mode(
                today
            ),
    )


def completion_rate(
    items,
    today,
):
    eligible = [
        item
        for item in items
        if item.status(today)
        != "past_exam"
    ]

    total = len(
        eligible
    )

    completed = sum(
        1
        for item in eligible
        if item.completed
    )

    percent = (
        None
        if total == 0
        else round(
            completed
            / total
            * 100,
            1,
        )
    )

    return {
        "completed": completed,
        "total": total,
        "percent": percent,
    }


def project_progress(
    items,
    today,
):
    return completion_rate(
        items,
        today,
    )


def nearest_exam(
    items,
    today,
):
    exams = [
        item
        for item in items
        if (
            isinstance(
                item,
                ExamItem,
            )
            and item.status(today)
            in (
                "today",
                "upcoming",
            )
        )
    ]

    if not exams:
        return None

    return min(
        exams,
        key=lambda item:
            item.due_date,
    )


def sort_by_attention(
    items,
    today,
):
    def sort_key(item):
        status = item.status(
            today
        )

        bucket = STATUS_BUCKET[
            status
        ]

        item_id = (
            item.id
            if item.id is not None
            else 10**12
        )

        if status == "overdue":
            return (
                bucket,
                PRIORITY_RANK[
                    item.priority
                ],
                -item.days_overdue(
                    today
                ),
                Decimal("0"),
                item_id,
            )

        return (
            bucket,
            0,
            0,
            -item.attention_score(
                today
            ),
            item_id,
        )

    return sorted(
        items,
        key=sort_key,
    )


def build_today_payload(
    items,
    today,
    area="all",
    exam_mode=False,
):
    items = list(
        items
    )

    filtered = select(
        items,
        by_area(area),
    )

    overdue = select(
        filtered,
        by_status(
            today,
            "overdue",
        ),
    )

    due_today = [
        item
        for item in filtered
        if (
            item.due_date == today
            and not item.is_past_exam(
                today
            )
        )
    ]

    progress = completion_rate(
        due_today,
        today,
    )

    next_exam = (
        None
        if area == "personal"
        else nearest_exam(
            filtered,
            today,
        )
    )

    hidden_by_exam_mode = 0

    if exam_mode:
        candidates = (
            overdue
            + due_today
        )

        hidden_by_exam_mode = sum(
            1
            for item in candidates
            if (
                not item.completed
                and item.status(today)
                != "past_exam"
                and not item.visible_in_exam_mode(
                    today
                )
            )
        )

        overdue = exam_mode_view(
            overdue,
            today,
        )

        due_today = exam_mode_view(
            due_today,
            today,
        )

    return {
        "progress": progress,

        "overdue":
            sort_by_attention(
                overdue,
                today,
            ),

        "today":
            sort_by_attention(
                due_today,
                today,
            ),

        "next_exam":
            next_exam,

        "hidden_by_exam_mode":
            hidden_by_exam_mode,
    }