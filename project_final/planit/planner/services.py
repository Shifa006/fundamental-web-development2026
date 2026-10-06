from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from .domain import (
    AssignmentItem,
    ExamItem,
    GeneralItem,
    GradeBook,
    GradeComponent,
    PersonalItem,
    PRIORITY_RANK,
    StudyItem,
)


ITEM_CLASSES = {
    ("academic", "general"): GeneralItem,
    ("academic", "assignment"): AssignmentItem,
    ("academic", "study"): StudyItem,
    ("academic", "exam"): ExamItem,
    ("personal", "general"): PersonalItem,
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
    item_class = ITEM_CLASSES.get((task.area, task.kind))

    if item_class is None:
        raise ValueError("Invalid task area and kind combination.")

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
    return list(filter(predicate, items))


def by_area(area):
    if area not in {"all", "academic", "personal"}:
        raise ValueError("Invalid area.")

    return lambda item: area == "all" or item.area == area


def by_status(today, *statuses):
    allowed = set(statuses)
    return lambda item: item.status(today) in allowed


def compose(*predicates):
    def combined(item):
        return all(predicate(item) for predicate in predicates)

    return combined


def exam_mode_view(items, today):
    return select(items, lambda item: item.visible_in_exam_mode(today))


def completion_rate(items, today):
    eligible = [item for item in items if item.status(today) != "past_exam"]
    total = len(eligible)
    completed = sum(1 for item in eligible if item.completed)

    return {
        "completed": completed,
        "total": total,
        "percent": None if total == 0 else round(completed / total * 100, 1),
    }


def project_progress(items, today):
    return completion_rate(items, today)


def subject_summary(items, today):
    statuses = [item.status(today) for item in items]

    return {
        "completion": completion_rate(items, today),
        "pending": sum(
            1
            for status in statuses
            if status in {"overdue", "today", "upcoming", "no_date"}
        ),
        "completed": statuses.count("completed"),
        "overdue": statuses.count("overdue"),
        "past_exams": statuses.count("past_exam"),
        "task_count": len(items),
    }


def nearest_exam(items, today):
    exams = [
        item
        for item in items
        if isinstance(item, ExamItem) and item.status(today) in {"today", "upcoming"}
    ]

    if not exams:
        return None

    return min(exams, key=lambda item: item.due_date)


def sort_by_attention(items, today):
    def sort_key(item):
        status = item.status(today)
        bucket = STATUS_BUCKET[status]
        item_id = item.id if item.id is not None else 10**12

        if status == "overdue":
            return (
                bucket,
                PRIORITY_RANK[item.priority],
                -item.days_overdue(today),
                Decimal("0"),
                item_id,
            )

        return (
            bucket,
            0,
            0,
            -item.attention_score(today),
            item_id,
        )

    return sorted(items, key=sort_key)


def group_by_date(items, week_start, week_end):
    grouped = {}
    current = week_start

    while current <= week_end:
        grouped[current] = []
        current += timedelta(days=1)

    for item in items:
        if item.due_date in grouped:
            grouped[item.due_date].append(item)

    return grouped


def build_today_payload(items, today, area="all", exam_mode=False):
    items = list(items)
    filtered = select(items, by_area(area))

    overdue = select(filtered, by_status(today, "overdue"))
    due_today = [
        item
        for item in filtered
        if item.due_date == today and not item.is_past_exam(today)
    ]

    progress = completion_rate(due_today, today)
    next_exam = None if area == "personal" else nearest_exam(filtered, today)
    hidden_by_exam_mode = 0

    if exam_mode:
        candidates = overdue + due_today
        hidden_by_exam_mode = sum(
            1
            for item in candidates
            if (
                not item.completed
                and item.status(today) != "past_exam"
                and not item.visible_in_exam_mode(today)
            )
        )
        overdue = exam_mode_view(overdue, today)
        due_today = exam_mode_view(due_today, today)

    return {
        "progress": progress,
        "overdue": sort_by_attention(overdue, today),
        "today": sort_by_attention(due_today, today),
        "next_exam": next_exam,
        "hidden_by_exam_mode": hidden_by_exam_mode,
    }


def to_json_number(value, places="0.01"):
    if value is None:
        return None

    quantized = value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return float(quantized)


def serialize_task(task, item, today, attention_rank=None):
    subject = None
    if task.subject is not None:
        subject = {
            "id": task.subject.id,
            "name": task.subject.name,
            "code": task.subject.code,
            "color": task.subject.color,
        }

    project = None
    if task.project is not None:
        project = {
            "id": task.project.id,
            "title": task.project.title,
        }

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "area": task.area,
        "kind": task.kind,
        "priority": task.priority,
        "priority_rank": PRIORITY_RANK[task.priority],
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "completed": task.completed,
        "status": item.status(today),
        "days_left": item.days_left(today),
        "days_overdue": item.days_overdue(today),
        "attention_score": to_json_number(item.attention_score(today)),
        "attention_rank": attention_rank,
        "exam_mode_visible": item.visible_in_exam_mode(today),
        "subject": subject,
        "project": project,
    }


def serialize_assessment(assessment):
    return {
        "id": assessment.id,
        "subject_id": assessment.subject_id,
        "name": assessment.name,
        "weight": to_json_number(assessment.weight),
        "max_score": to_json_number(assessment.max_score),
        "score": to_json_number(assessment.score),
    }


def serialize_subject(subject):
    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "semester": subject.semester,
        "color": subject.color,
    }


def serialize_project(project, progress=None):
    subject = None
    if project.subject is not None:
        subject = {
            "id": project.subject.id,
            "name": project.subject.name,
            "code": project.subject.code,
            "color": project.subject.color,
        }

    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "due_date": project.due_date.isoformat() if project.due_date else None,
        "subject": subject,
        "progress": progress,
    }


def build_gradebook(assessments):
    return GradeBook(
        GradeComponent(
            assessment.name,
            assessment.weight,
            assessment.max_score,
            assessment.score,
        )
        for assessment in assessments
    )


def grade_overview(assessments, target):
    book = build_gradebook(assessments)
    result = book.required_average(target)

    return {
        "configured_weight": to_json_number(book.configured_weight),
        "graded_weight": to_json_number(book.graded_weight),
        "earned_course_points": to_json_number(book.earned_course_points),
        "average_on_graded_work": to_json_number(book.average_on_graded_work),
        "target": to_json_number(Decimal(str(target))),
        "status": result["status"],
        "required": to_json_number(result["required"]),
    }
