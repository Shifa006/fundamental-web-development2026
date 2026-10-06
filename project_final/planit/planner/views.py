from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import (
    ensure_csrf_cookie,
)

from .domain import EXAM_WINDOW_DAYS
from .models import Task
from .services import (
    build_today_payload,
    by_area,
    group_by_date,
    select,
    serialize_task,
    sort_by_attention,
    to_domain_item,
)


# --------------------------------------------------
# Page views
# --------------------------------------------------

@ensure_csrf_cookie
def today_page(request):
    return render(
        request,
        "planner/today.html",
    )


@ensure_csrf_cookie
def tasks_page(request):
    return render(
        request,
        "planner/tasks.html",
    )


@ensure_csrf_cookie
def courses_page(request):
    return render(
        request,
        "planner/courses.html",
    )


@ensure_csrf_cookie
def projects_page(request):
    return render(
        request,
        "planner/projects.html",
    )


# --------------------------------------------------
# API helpers
# --------------------------------------------------

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
        {
            "error": error
        },
        status=status,
    )


def method_not_allowed():
    response = api_error(
        "method_not_allowed",
        "This endpoint accepts GET requests only.",
        status=405,
    )

    response["Allow"] = "GET"

    return response


def parse_common_filters(request):
    area = request.GET.get(
        "area",
        "all",
    )

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

    if raw_exam_mode not in {
        "0",
        "1",
    }:
        raise ValueError(
            "Exam mode must be 0 or 1."
        )

    exam_mode = (
        raw_exam_mode == "1"
    )

    return area, exam_mode


def build_meta(
    today,
    week_start=None,
    week_end=None,
):
    if week_start is None:
        week_start = (
            today
            - timedelta(
                days=today.weekday()
            )
        )

    if week_end is None:
        week_end = (
            week_start
            + timedelta(days=6)
        )

    return {
        "today":
            today.isoformat(),

        "week_start":
            week_start.isoformat(),

        "week_end":
            week_end.isoformat(),

        "timezone":
            settings.TIME_ZONE,

        "exam_window_days":
            EXAM_WINDOW_DAYS,
    }


def task_queryset():
    return (
        Task.objects
        .select_related(
            "subject",
            "project",
        )
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
        for rank, item
        in enumerate(
            items,
            start=1,
        )
    ]


# --------------------------------------------------
# GET /api/tasks/
# --------------------------------------------------

def tasks_api(request):
    if request.method != "GET":
        return method_not_allowed()

    today = timezone.localdate()

    tasks = list(
        task_queryset()
    )

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
            "meta":
                build_meta(today),

            "tasks":
                serialize_items(
                    ordered,
                    task_lookup,
                    today,
                ),
        }
    )


# --------------------------------------------------
# GET /api/today/
# --------------------------------------------------

def today_api(request):
    if request.method != "GET":
        return method_not_allowed()

    try:
        area, exam_mode = (
            parse_common_filters(
                request
            )
        )
    except ValueError as error:
        return api_error(
            "invalid_query_parameter",
            str(error),
        )

    today = timezone.localdate()

    tasks = list(
        task_queryset()
    )

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
                payload[
                    "next_exam"
                ].id
            ],
            payload[
                "next_exam"
            ],
            today,
        )
        if payload["next_exam"]
        else None
    )

    return JsonResponse(
        {
            "meta":
                build_meta(today),

            "progress":
                payload[
                    "progress"
                ],

            "overdue":
                serialize_items(
                    payload[
                        "overdue"
                    ],
                    task_lookup,
                    today,
                ),

            "today":
                serialize_items(
                    payload[
                        "today"
                    ],
                    task_lookup,
                    today,
                ),

            "next_exam":
                next_exam,

            "hidden_by_exam_mode":
                payload[
                    "hidden_by_exam_mode"
                ],
        }
    )


# --------------------------------------------------
# GET /api/week/
# --------------------------------------------------

def week_api(request):
    if request.method != "GET":
        return method_not_allowed()

    try:
        area, exam_mode = (
            parse_common_filters(
                request
            )
        )
    except ValueError as error:
        return api_error(
            "invalid_query_parameter",
            str(error),
        )

    today = timezone.localdate()

    week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

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
                "date":
                    current.isoformat(),

                "weekday":
                    current.strftime(
                        "%A"
                    ),

                "tasks":
                    serialize_items(
                        ordered,
                        task_lookup,
                        today,
                    ),
            }
        )

        current += timedelta(
            days=1
        )

    return JsonResponse(
        {
            "meta":
                build_meta(
                    today,
                    week_start,
                    week_end,
                ),

            "days":
                days,
        }
    )