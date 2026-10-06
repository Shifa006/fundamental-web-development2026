"""v1.3 endpoints: settings, modules, month view, duplicate task."""
from datetime import date

from django.http import JsonResponse
from django.utils import timezone

from .models import Subject, UserSettings
from .modules import MODULE_REGISTRY
from .services import (
    by_area,
    day_dots,
    group_by_date,
    month_bounds,
    select,
    sort_by_attention,
    to_domain_item,
)
from .validators import PlanitValidationError, validate_allowed_fields
from .views import (
    build_meta,
    method_not_allowed,
    parse_common_filters,
    read_json_body,
    serialize_items,
    task_queryset,
    validation_response,
)

SETTINGS_INPUT_FIELDS = {"enabled_modules", "onboarding_done"}


def get_user_settings(user):
    settings_row, _ = UserSettings.objects.get_or_create(user=user)
    return settings_row


def serialize_settings(row):
    return {
        "enabled_modules": list(row.enabled_modules),
        "onboarding_done": row.onboarding_done,
        "defaults": task_defaults(row),
    }


def task_defaults(row):
    return {
        "area": row.last_area,
        "kind": row.last_kind,
        "priority": row.last_priority,
        "subject_id": row.last_subject_id,
    }


def remember_task_defaults(user, task):
    """Store the last-used form values (called after a task is created)."""
    row = get_user_settings(user)
    row.last_area = task.area
    row.last_kind = task.kind
    row.last_priority = task.priority
    row.last_subject = task.subject
    row.save(update_fields=["last_area", "last_kind", "last_priority", "last_subject"])


def validate_enabled_modules(value):
    if not isinstance(value, list) or not all(isinstance(key, str) for key in value):
        raise PlanitValidationError(
            "enabled_modules must be a list of module keys.",
            code="invalid_modules",
            field="enabled_modules",
        )
    for key in value:
        if key not in MODULE_REGISTRY:
            raise PlanitValidationError(
                f"Unknown module: {key}",
                code="unknown_module",
                field="enabled_modules",
            )
    return list(dict.fromkeys(value))  # de-duplicate, keep order


def settings_api(request):
    row = get_user_settings(request.user)

    if request.method == "GET":
        return JsonResponse({"settings": serialize_settings(row)})

    if request.method == "PATCH":
        try:
            payload = read_json_body(request)
            validate_allowed_fields(payload, SETTINGS_INPUT_FIELDS)
            if "enabled_modules" in payload:
                row.enabled_modules = validate_enabled_modules(payload["enabled_modules"])
            if "onboarding_done" in payload:
                if not isinstance(payload["onboarding_done"], bool):
                    raise PlanitValidationError(
                        "onboarding_done must be true or false.",
                        code="invalid_onboarding",
                        field="onboarding_done",
                    )
                row.onboarding_done = payload["onboarding_done"]
        except PlanitValidationError as error:
            return validation_response(error)
        row.save()
        return JsonResponse({"settings": serialize_settings(row)})

    return method_not_allowed("GET", "PATCH")


def modules_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")
    enabled = set(get_user_settings(request.user).enabled_modules)
    return JsonResponse(
        {
            "modules": [
                module.describe(module.key in enabled)
                for module in MODULE_REGISTRY.values()
            ]
        }
    )


def parse_month_params(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except ValueError:
        raise PlanitValidationError(
            "Year and month must be numbers.",
            code="invalid_query_parameter",
            field="month",
        )
    if not 2000 <= year <= 2100 or not 1 <= month <= 12:
        raise PlanitValidationError(
            "Month must be 1-12 and year 2000-2100.",
            code="invalid_query_parameter",
            field="month",
        )
    return year, month


def month_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        area, exam_mode = parse_common_filters(request)
        year, month = parse_month_params(request)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    start, end = month_bounds(year, month)

    tasks = list(task_queryset(request.user).filter(due_date__range=(start, end)))
    task_lookup = {task.id: task for task in tasks}
    items = select([to_domain_item(task) for task in tasks], by_area(area))
    if exam_mode:
        items = [
            item for item in items
            if item.status(today) == "past_exam" or item.visible_in_exam_mode(today)
        ]

    grouped = group_by_date(items, start, end)
    days = []
    for day in sorted(grouped):
        day_items = sort_by_attention(grouped[day], today)
        statuses = [item.status(today) for item in day_items]
        days.append(
            {
                "date": day.isoformat(),
                "counts": {
                    "total": len(day_items),
                    "exam": sum(1 for item in day_items if item.kind == "exam"),
                    "overdue": statuses.count("overdue"),
                    "completed": statuses.count("completed"),
                },
                "dots": day_dots(day_items, today),
                "tasks": serialize_items(day_items, task_lookup, today),
            }
        )

    overdue_before = sum(
        1
        for task in task_queryset(request.user).filter(due_date__lt=start, completed=False)
        if to_domain_item(task).status(today) == "overdue"
    )

    return JsonResponse(
        {
            "meta": build_meta(today),
            "year": year,
            "month": month,
            "first_weekday": date(year, month, 1).weekday(),
            "overdue_before_month": overdue_before,
            "days": days,
        }
    )


def parse_review_offsets(value):
    if value is None:
        return []
    if (
        not isinstance(value, list)
        or len(value) > 5
        or not all(isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 30 for v in value)
    ):
        raise PlanitValidationError(
            "review_offsets must be up to 5 whole numbers between 1 and 30.",
            code="invalid_review_offsets",
            field="review_offsets",
        )
    return value


def create_review_tasks(user, exam, today, offsets):
    """Create "Review: <exam>" study tasks before an exam. Returns how many."""
    from .models import Task
    from .services import plan_review_tasks

    created = 0
    for plan in plan_review_tasks(exam.title, exam.due_date, today, offsets):
        Task.objects.create(
            owner=user,
            title=plan["title"],
            area="academic",
            kind="study",
            priority="normal",
            due_date=plan["due_date"],
            subject=exam.subject,
        )
        created += 1
    return created
