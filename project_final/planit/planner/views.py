import json
from datetime import timedelta
from json import JSONDecodeError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from .domain import EXAM_WINDOW_DAYS
from .models import Project, Subject, Task
from .services import (
    build_today_payload,
    by_area,
    group_by_date,
    select,
    serialize_task,
    sort_by_attention,
    to_domain_item,
)
from .validators import (
    TaskValidationError,
    normalize_task_data,
    validate_allowed_fields,
)


# --------------------------------------------------
# Page views
# --------------------------------------------------

@ensure_csrf_cookie
def today_page(request):
    return render(request, "planner/today.html")


@ensure_csrf_cookie
def tasks_page(request):
    return render(request, "planner/tasks.html")


@ensure_csrf_cookie
def courses_page(request):
    return render(request, "planner/courses.html")


@ensure_csrf_cookie
def projects_page(request):
    return render(request, "planner/projects.html")


# --------------------------------------------------
# API helpers
# --------------------------------------------------

def read_json_body(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        raise TaskValidationError(
            "Request body must contain valid JSON.",
            code="invalid_json",
        )

    if not isinstance(data, dict):
        raise TaskValidationError(
            "JSON body must be an object.",
            code="invalid_json",
        )

    return data


def api_error(
    code,
    message,
    status=400,
    field=None,
):
    error = {
        "code": code,
        "message": message,
    }

    if field is not None:
        error["field"] = field

    return JsonResponse(
        {"error": error},
        status=status,
    )


def method_not_allowed(*allowed):
    methods = ", ".join(allowed)

    response = api_error(
        "method_not_allowed",
        f"This endpoint accepts {methods}.",
        status=405,
    )
    response["Allow"] = methods

    return response


def parse_common_filters(request):
    area = request.GET.get("area", "all")

    if area not in {
        "all",
        "academic",
        "personal",
    }:
        raise ValueError(
            "Area must be all, academic, or personal."
        )

    raw_exam_mode = request.GET.get(
        "exam_mode",
        "0",
    )

    if raw_exam_mode not in {"0", "1"}:
        raise ValueError(
            "Exam mode must be 0 or 1."
        )

    return area, raw_exam_mode == "1"


def build_meta(
    today,
    week_start=None,
    week_end=None,
):
    if week_start is None:
        week_start = today - timedelta(
            days=today.weekday()
        )

    if week_end is None:
        week_end = week_start + timedelta(days=6)

    return {
        "today": today.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "timezone": settings.TIME_ZONE,
        "exam_window_days": EXAM_WINDOW_DAYS,
    }


def task_queryset():
    return Task.objects.select_related(
        "subject",
        "project",
    )


def serialize_items(
    items,
    task_lookup,
    today,
):
    return [
        serialize_task(
            task_lookup[item.id],
            item,
            today,
            attention_rank=rank,
        )
        for rank, item in enumerate(
            items,
            start=1,
        )
    ]


def task_input_data(task):
    return {
        "title": task.title,
        "description": task.description,
        "area": task.area,
        "kind": task.kind,
        "priority": task.priority,
        "due_date": task.due_date,
        "completed": task.completed,
        "subject_id": task.subject_id,
        "project_id": task.project_id,
    }


def resolve_task_relations(data):
    subject = None
    project = None

    subject_id = data["subject_id"]

    if subject_id is not None:
        try:
            subject = Subject.objects.get(
                pk=subject_id
            )
        except Subject.DoesNotExist:
            raise TaskValidationError(
                "Subject was not found.",
                code="subject_not_found",
                field="subject_id",
                status=404,
            )

    project_id = data["project_id"]

    if project_id is not None:
        try:
            project = (
                Project.objects
                .select_related("subject")
                .get(pk=project_id)
            )
        except Project.DoesNotExist:
            raise TaskValidationError(
                "Project was not found.",
                code="project_not_found",
                field="project_id",
                status=404,
            )

    # A project with a subject defines the task subject.
    if (
        project is not None
        and project.subject_id is not None
    ):
        if subject is None:
            subject = project.subject
            data["subject_id"] = project.subject_id
        elif subject.id != project.subject_id:
            raise TaskValidationError(
                "Task subject must match the project subject.",
                code="project_subject_mismatch",
                field="subject_id",
            )

    if (
        data["area"] == "personal"
        and subject is not None
    ):
        raise TaskValidationError(
            "Personal tasks cannot belong to an academic subject.",
            code="personal_subject_not_allowed",
            field="subject_id",
        )

    return subject, project


def _model_validation_error(error):
    field = None
    message = "Task data is invalid."

    if hasattr(error, "message_dict"):
        message_dict = error.message_dict

        if message_dict:
            field = next(iter(message_dict))
            messages = message_dict[field]

            if messages:
                message = messages[0]

    elif getattr(error, "messages", None):
        message = error.messages[0]

    return TaskValidationError(
        message,
        code="model_validation_error",
        field=field,
    )


def apply_task_data(
    task,
    data,
    subject,
    project,
):
    task.title = data["title"]
    task.description = data["description"]
    task.area = data["area"]
    task.kind = data["kind"]
    task.priority = data["priority"]
    task.due_date = data["due_date"]
    task.completed = data["completed"]
    task.subject = subject
    task.project = project

    try:
        task.full_clean()
    except ValidationError as error:
        raise _model_validation_error(error)

    task.save()
    return task


# --------------------------------------------------
# Task collection API
# GET  /api/tasks/
# POST /api/tasks/
# --------------------------------------------------

def get_tasks_api(request):
    today = timezone.localdate()

    tasks = list(task_queryset())
    task_lookup = {
        task.id: task
        for task in tasks
    }

    items = [
        to_domain_item(task)
        for task in tasks
    ]

    ordered = sort_by_attention(
        items,
        today,
    )

    return JsonResponse(
        {
            "meta": build_meta(today),
            "tasks": serialize_items(
                ordered,
                task_lookup,
                today,
            ),
        }
    )


def create_task_api(request):
    try:
        payload = read_json_body(request)
        validate_allowed_fields(payload)

        merged = {
            "title": "",
            "description": "",
            "area": "academic",
            "kind": "general",
            "priority": "normal",
            "due_date": None,
            "completed": False,
            "subject_id": None,
            "project_id": None,
        }
        merged.update(payload)

        data = normalize_task_data(merged)
        subject, project = resolve_task_relations(
            data
        )

        task = Task()
        apply_task_data(
            task,
            data,
            subject,
            project,
        )

    except TaskValidationError as error:
        return api_error(
            error.code,
            str(error),
            status=error.status,
            field=error.field,
        )

    today = timezone.localdate()
    item = to_domain_item(task)

    return JsonResponse(
        {
            "task": serialize_task(
                task,
                item,
                today,
            ),
        },
        status=201,
    )


def tasks_api(request):
    if request.method == "GET":
        return get_tasks_api(request)

    if request.method == "POST":
        return create_task_api(request)

    return method_not_allowed(
        "GET",
        "POST",
    )


# --------------------------------------------------
# Task detail API
# PATCH  /api/tasks/<id>/
# DELETE /api/tasks/<id>/
# --------------------------------------------------

def update_task_api(
    request,
    task,
):
    try:
        payload = read_json_body(request)
        validate_allowed_fields(payload)

        merged = task_input_data(task)
        merged.update(payload)

        data = normalize_task_data(merged)
        subject, project = resolve_task_relations(
            data
        )

        apply_task_data(
            task,
            data,
            subject,
            project,
        )

    except TaskValidationError as error:
        return api_error(
            error.code,
            str(error),
            status=error.status,
            field=error.field,
        )

    today = timezone.localdate()
    item = to_domain_item(task)

    return JsonResponse(
        {
            "task": serialize_task(
                task,
                item,
                today,
            ),
        }
    )


def task_detail_api(
    request,
    task_id,
):
    try:
        task = (
            Task.objects
            .select_related(
                "subject",
                "project",
            )
            .get(pk=task_id)
        )
    except Task.DoesNotExist:
        return api_error(
            "task_not_found",
            "Task was not found.",
            status=404,
        )

    if request.method == "PATCH":
        return update_task_api(
            request,
            task,
        )

    if request.method == "DELETE":
        task.delete()
        return HttpResponse(status=204)

    return method_not_allowed(
        "PATCH",
        "DELETE",
    )


# --------------------------------------------------
# GET /api/task-options/
# --------------------------------------------------

def task_options_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    subjects = list(
        Subject.objects
        .order_by("name")
        .values(
            "id",
            "name",
            "code",
        )
    )

    projects = [
        {
            "id": project.id,
            "title": project.title,
            "subject_id": project.subject_id,
        }
        for project in Project.objects
        .order_by("title")
    ]

    return JsonResponse(
        {
            "subjects": subjects,
            "projects": projects,
        }
    )


# --------------------------------------------------
# GET /api/today/
# --------------------------------------------------

def today_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        area, exam_mode = parse_common_filters(
            request
        )
    except ValueError as error:
        return api_error(
            "invalid_query_parameter",
            str(error),
        )

    today = timezone.localdate()

    tasks = list(task_queryset())
    task_lookup = {
        task.id: task
        for task in tasks
    }

    items = [
        to_domain_item(task)
        for task in tasks
    ]

    payload = build_today_payload(
        items,
        today,
        area=area,
        exam_mode=exam_mode,
    )

    next_exam = (
        serialize_task(
            task_lookup[
                payload["next_exam"].id
            ],
            payload["next_exam"],
            today,
        )
        if payload["next_exam"]
        else None
    )

    return JsonResponse(
        {
            "meta": build_meta(today),
            "progress": payload["progress"],
            "overdue": serialize_items(
                payload["overdue"],
                task_lookup,
                today,
            ),
            "today": serialize_items(
                payload["today"],
                task_lookup,
                today,
            ),
            "next_exam": next_exam,
            "hidden_by_exam_mode": (
                payload[
                    "hidden_by_exam_mode"
                ]
            ),
        }
    )


# --------------------------------------------------
# GET /api/week/
# --------------------------------------------------

def week_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        area, exam_mode = parse_common_filters(
            request
        )
    except ValueError as error:
        return api_error(
            "invalid_query_parameter",
            str(error),
        )

    today = timezone.localdate()

    week_start = today - timedelta(
        days=today.weekday()
    )
    week_end = week_start + timedelta(days=6)

    tasks = list(
        task_queryset().filter(
            due_date__range=(
                week_start,
                week_end,
            )
        )
    )

    task_lookup = {
        task.id: task
        for task in tasks
    }

    items = [
        to_domain_item(task)
        for task in tasks
    ]

    items = select(
        items,
        by_area(area),
    )

    if exam_mode:
        items = [
            item
            for item in items
            if (
                item.status(today)
                == "past_exam"
                or item.visible_in_exam_mode(
                    today
                )
            )
        ]

    grouped = group_by_date(
        items,
        week_start,
        week_end,
    )

    days = []
    current = week_start

    while current <= week_end:
        ordered = sort_by_attention(
            grouped[current],
            today,
        )

        days.append(
            {
                "date": current.isoformat(),
                "weekday": current.strftime(
                    "%A"
                ),
                "tasks": serialize_items(
                    ordered,
                    task_lookup,
                    today,
                ),
            }
        )

        current += timedelta(days=1)

    return JsonResponse(
        {
            "meta": build_meta(
                today,
                week_start,
                week_end,
            ),
            "days": days,
        }
    )
