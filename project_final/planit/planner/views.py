import json
from datetime import timedelta
from json import JSONDecodeError

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .domain import EXAM_WINDOW_DAYS
from .modules import build_module_cards
from .forms import SignUpForm
from .models import Assessment, Project, Subject, Task
from .services import (
    build_today_payload,
    by_area,
    default_assessments,
    grade_overview,
    group_by_date,
    project_progress,
    select,
    serialize_assessment,
    serialize_project,
    serialize_subject,
    serialize_task,
    should_suggest_exam_mode,
    sort_by_attention,
    subject_summary,
    to_domain_item,
    to_domain_items,
)
from .validators import (
    ASSESSMENT_INPUT_FIELDS,
    PROJECT_INPUT_FIELDS,
    SUBJECT_INPUT_FIELDS,
    TASK_INPUT_FIELDS,
    PlanitValidationError,
    normalize_assessment_data,
    normalize_project_data,
    normalize_subject_data,
    normalize_target,
    normalize_task_data,
    validate_allowed_fields,
)


# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------

@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("today")

    next_url = request.POST.get("next") or request.GET.get("next") or ""
    context = {
        "error": "",
        "username": "",
        "next": next_url,
    }

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        context["username"] = username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("today")

        context["error"] = "Incorrect username or password."

    return render(request, "planner/login.html", context)


@ensure_csrf_cookie
def signup_page(request):
    if request.user.is_authenticated:
        return redirect("today")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)  # auto sign-in after registration
        return redirect("today")

    return render(request, "planner/signup.html", {"form": form})


@require_POST
def logout_page(request):
    logout(request)
    return redirect("login")


# -----------------------------------------------------------------------------
# Page views
# -----------------------------------------------------------------------------

def page_context(page_name):
    return {
        "page_name": page_name,
        "server_today": timezone.localdate().isoformat(),
    }


@ensure_csrf_cookie
def today_page(request):
    return render(request, "planner/today.html", page_context("today"))


@ensure_csrf_cookie
def tasks_page(request):
    return render(request, "planner/tasks.html", page_context("tasks"))


@ensure_csrf_cookie
def courses_page(request):
    return render(request, "planner/courses.html", page_context("courses"))


@ensure_csrf_cookie
def projects_page(request):
    return render(request, "planner/projects.html", page_context("projects"))


# -----------------------------------------------------------------------------
# API helpers
# -----------------------------------------------------------------------------

def api_error(code, message, status=400, field=None):
    error = {
        "code": code,
        "message": message,
    }

    if field is not None:
        error["field"] = field

    return JsonResponse({"error": error}, status=status)


def method_not_allowed(*allowed):
    methods = ", ".join(allowed)
    response = api_error(
        "method_not_allowed",
        f"This endpoint accepts {methods}.",
        status=405,
    )
    response["Allow"] = methods
    return response


def read_json_body(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        raise PlanitValidationError(
            "Request body must contain valid JSON.",
            code="invalid_json",
        )

    if not isinstance(data, dict):
        raise PlanitValidationError(
            "JSON body must be an object.",
            code="invalid_json",
        )

    return data


def model_validation_error(error):
    if hasattr(error, "message_dict") and error.message_dict:
        field, messages = next(iter(error.message_dict.items()))
        message = messages[0] if messages else "Data is invalid."
        return PlanitValidationError(
            message,
            code="model_validation_error",
            field=None if field == "__all__" else field,
        )

    return PlanitValidationError(
        "Data is invalid.",
        code="model_validation_error",
    )


def validation_response(error):
    return api_error(
        error.code,
        str(error),
        status=error.status,
        field=error.field,
    )


def parse_common_filters(request):
    area = request.GET.get("area", "all")

    if area not in {"all", "academic", "personal"}:
        raise PlanitValidationError(
            "Area must be all, academic, or personal.",
            code="invalid_query_parameter",
            field="area",
        )

    raw_exam_mode = request.GET.get("exam_mode", "0")

    if raw_exam_mode not in {"0", "1"}:
        raise PlanitValidationError(
            "Exam mode must be 0 or 1.",
            code="invalid_query_parameter",
            field="exam_mode",
        )

    return area, raw_exam_mode == "1"


def build_meta(today, week_start=None, week_end=None):
    if week_start is None:
        week_start = today - timedelta(days=today.weekday())

    if week_end is None:
        week_end = week_start + timedelta(days=6)

    return {
        "today": today.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "timezone": settings.TIME_ZONE,
        "exam_window_days": EXAM_WINDOW_DAYS,
    }


def task_queryset(user=None):
    qs = Task.objects.select_related("subject", "project")
    return qs.filter(owner=user) if user is not None else qs


def serialize_items(items, task_lookup, today):
    return [
        serialize_task(
            task_lookup[item.id],
            item,
            today,
            attention_rank=rank,
        )
        for rank, item in enumerate(items, start=1)
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


def subject_input_data(subject):
    return {
        "name": subject.name,
        "code": subject.code,
        "semester": subject.semester,
        "color": subject.color,
    }


def project_input_data(project):
    return {
        "title": project.title,
        "description": project.description,
        "due_date": project.due_date,
        "subject_id": project.subject_id,
    }


def assessment_input_data(assessment):
    return {
        "subject_id": assessment.subject_id,
        "name": assessment.name,
        "weight": assessment.weight,
        "max_score": assessment.max_score,
        "score": assessment.score,
    }


def get_subject(user, subject_id):
    try:
        return Subject.objects.get(pk=subject_id, owner=user)
    except Subject.DoesNotExist:
        raise PlanitValidationError(
            "Subject was not found.",
            code="subject_not_found",
            field="subject_id",
            status=404,
        )


def get_project(user, project_id):
    try:
        return Project.objects.select_related("subject").get(pk=project_id, owner=user)
    except Project.DoesNotExist:
        raise PlanitValidationError(
            "Project was not found.",
            code="project_not_found",
            field="project_id",
            status=404,
        )


def get_task(user, task_id):
    try:
        return task_queryset(user).get(pk=task_id)
    except Task.DoesNotExist:
        raise PlanitValidationError(
            "Task was not found.",
            code="task_not_found",
            status=404,
        )


def get_assessment(user, assessment_id):
    try:
        return Assessment.objects.select_related("subject").get(pk=assessment_id, subject__owner=user)
    except Assessment.DoesNotExist:
        raise PlanitValidationError(
            "Assessment was not found.",
            code="assessment_not_found",
            status=404,
        )


def resolve_task_relations(user, data):
    subject = None
    project = None

    if data["subject_id"] is not None:
        subject = get_subject(user, data["subject_id"])

    if data["project_id"] is not None:
        project = get_project(user, data["project_id"])

    if project is not None and project.subject_id is not None:
        if subject is None:
            subject = project.subject
            data["subject_id"] = project.subject_id
        elif subject.id != project.subject_id:
            raise PlanitValidationError(
                "Task subject must match the project subject.",
                code="project_subject_mismatch",
                field="subject_id",
            )

    return subject, project


def apply_task_data(task, data, subject, project):
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
        raise model_validation_error(error)

    task.save()
    return task


def apply_subject_data(subject, data):
    subject.name = data["name"]
    subject.code = data["code"]
    subject.semester = data["semester"]
    subject.color = data["color"]

    try:
        subject.full_clean()
    except ValidationError as error:
        raise model_validation_error(error)

    subject.save()
    return subject


def apply_project_data(project, data, subject):
    project.title = data["title"]
    project.description = data["description"]
    project.due_date = data["due_date"]
    project.subject = subject

    try:
        project.full_clean()
    except ValidationError as error:
        raise model_validation_error(error)

    project.save()
    return project


def validate_assessment_total(subject_id, weight, assessment_id=None):
    assessments = Assessment.objects.filter(subject_id=subject_id)

    if assessment_id is not None:
        assessments = assessments.exclude(pk=assessment_id)

    current_total = sum(
        (assessment.weight for assessment in assessments),
        start=0,
    )

    if current_total + weight > 100:
        available = 100 - current_total
        raise PlanitValidationError(
            f"Total weight would exceed 100. You can add at most {available} more.",
            code="weight_exceeded",
            field="weight",
        )


def apply_assessment_data(assessment, data, subject):
    assessment.subject = subject
    assessment.name = data["name"]
    assessment.weight = data["weight"]
    assessment.max_score = data["max_score"]
    assessment.score = data["score"]

    try:
        assessment.full_clean()
    except ValidationError as error:
        raise model_validation_error(error)

    assessment.save()
    return assessment


def project_progress_for_model(project, today):
    items = to_domain_items(project.tasks.all())
    return project_progress(items, today)


def subject_payload(subject, today, include_detail=False):
    prefetch_cache = getattr(subject, "_prefetched_objects_cache", {})

    if "tasks" in prefetch_cache and not include_detail:
        tasks = list(prefetch_cache["tasks"])
    else:
        tasks = list(task_queryset().filter(subject=subject))

    if "assessments" in prefetch_cache:
        assessments = list(prefetch_cache["assessments"])
    else:
        assessments = list(subject.assessments.all())

    items = to_domain_items(tasks)
    summary = subject_summary(items, today)

    payload = {
        **serialize_subject(subject),
        "summary": summary,
        "assessment_count": len(assessments),
    }

    if include_detail:
        task_lookup = {task.id: task for task in tasks}
        ordered = sort_by_attention(items, today)
        payload["tasks"] = serialize_items(ordered, task_lookup, today)
        payload["assessments"] = [
            serialize_assessment(assessment)
            for assessment in assessments
        ]
        payload["delete_impact"] = {
            "assessments_deleted": len(assessments),
            "tasks_detached": len(tasks),
            "projects_detached": subject.projects.count(),
        }

    return payload


def project_payload(project, today, include_detail=False):
    progress = project_progress_for_model(project, today)
    payload = serialize_project(project, progress=progress)

    if include_detail:
        tasks = list(task_queryset().filter(project=project))
        items = to_domain_items(tasks)
        task_lookup = {task.id: task for task in tasks}
        payload["tasks"] = serialize_items(
            sort_by_attention(items, today),
            task_lookup,
            today,
        )
        payload["delete_impact"] = {
            "tasks_detached": project.tasks.count(),
        }

    return payload


# -----------------------------------------------------------------------------
# Tasks / Today / Week
# -----------------------------------------------------------------------------

def tasks_api(request):
    if request.method == "GET":
        return get_tasks_api(request)
    if request.method == "POST":
        return create_task_api(request)
    return method_not_allowed("GET", "POST")


def get_tasks_api(request):
    today = timezone.localdate()
    tasks = list(task_queryset(request.user))
    task_lookup = {task.id: task for task in tasks}
    items = to_domain_items(tasks)
    ordered = sort_by_attention(items, today)

    return JsonResponse(
        {
            "meta": build_meta(today),
            "tasks": serialize_items(ordered, task_lookup, today),
        }
    )


def create_task_api(request):
    review_tasks_created = 0

    try:
        payload = read_json_body(request)
        from .views_extra import parse_review_offsets
        review_offsets = parse_review_offsets(payload.pop("review_offsets", None))
        validate_allowed_fields(payload, TASK_INPUT_FIELDS)

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
        subject, project = resolve_task_relations(request.user, data)
        task = apply_task_data(Task(owner=request.user), data, subject, project)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    item = to_domain_item(task)

    from .views_extra import create_review_tasks, remember_task_defaults
    remember_task_defaults(request.user, task)
    if review_offsets and task.kind == "exam" and task.due_date:
        review_tasks_created = create_review_tasks(request.user, task, today, review_offsets)

    return JsonResponse(
        {
            "task": serialize_task(task, item, today),
            "review_tasks_created": review_tasks_created,
        },
        status=201,
    )


def task_detail_api(request, task_id):
    try:
        task = get_task(request.user, task_id)
    except PlanitValidationError as error:
        return validation_response(error)

    if request.method == "PATCH":
        return update_task_api(request, task)

    if request.method == "DELETE":
        task.delete()
        return HttpResponse(status=204)

    return method_not_allowed("PATCH", "DELETE")


@require_POST
def task_duplicate_api(request, task_id):
    try:
        task = get_task(request.user, task_id)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    data = task_input_data(task)
    data["completed"] = False
    if data.get("due_date") is not None:
        data["due_date"] = today
    try:
        data = normalize_task_data(data)
        subject, project = resolve_task_relations(request.user, data)
        copy = apply_task_data(Task(owner=request.user), data, subject, project)
    except PlanitValidationError as error:
        return validation_response(error)

    return JsonResponse({"task": serialize_task(copy, to_domain_item(copy), today)}, status=201)


def update_task_api(request, task):
    try:
        payload = read_json_body(request)
        validate_allowed_fields(payload, TASK_INPUT_FIELDS)
        merged = task_input_data(task)
        merged.update(payload)
        data = normalize_task_data(merged)
        subject, project = resolve_task_relations(request.user, data)
        apply_task_data(task, data, subject, project)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    return JsonResponse(
        {"task": serialize_task(task, to_domain_item(task), today)}
    )


def task_options_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    subjects = [
        serialize_subject(subject)
        for subject in Subject.objects.filter(owner=request.user)
    ]
    projects = [
        serialize_project(project)
        for project in Project.objects.filter(owner=request.user).select_related("subject")
    ]

    from .views_extra import get_user_settings, task_defaults

    return JsonResponse(
        {
            "subjects": subjects,
            "projects": projects,
            "defaults": task_defaults(get_user_settings(request.user)),
        }
    )


def today_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        area, exam_mode = parse_common_filters(request)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    tasks = list(task_queryset(request.user))
    task_lookup = {task.id: task for task in tasks}
    items = to_domain_items(tasks)
    payload = build_today_payload(
        items,
        today,
        area=area,
        exam_mode=exam_mode,
    )

    next_exam = None
    if payload["next_exam"] is not None:
        item = payload["next_exam"]
        next_exam = serialize_task(task_lookup[item.id], item, today)

    top_focus = None
    if payload["top_focus"] is not None:
        item = payload["top_focus"]
        top_focus = serialize_task(task_lookup[item.id], item, today)

    return JsonResponse(
        {
            "meta": build_meta(today),
            "progress": payload["progress"],
            "overdue": serialize_items(payload["overdue"], task_lookup, today),
            "today": serialize_items(payload["today"], task_lookup, today),
            "next_exam": next_exam,
            "top_focus": top_focus,
            "hidden_by_exam_mode": payload["hidden_by_exam_mode"],
            "suggest_exam_mode": should_suggest_exam_mode(items, today) and not exam_mode,
            "modules": build_module_cards(
                _user_settings(request.user).enabled_modules,
                request.user,
                today,
                exam_mode=exam_mode,
            ),
        }
    )


def week_api(request):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        area, exam_mode = parse_common_filters(request)
    except PlanitValidationError as error:
        return validation_response(error)

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    tasks = list(
        task_queryset(request.user).filter(due_date__range=(week_start, week_end))
    )
    task_lookup = {task.id: task for task in tasks}
    items = to_domain_items(tasks)
    items = select(items, by_area(area))

    if exam_mode:
        items = [
            item
            for item in items
            if item.status(today) == "past_exam" or item.visible_in_exam_mode(today)
        ]

    grouped = group_by_date(items, week_start, week_end)
    days = []
    current = week_start

    while current <= week_end:
        ordered = sort_by_attention(grouped[current], today)
        days.append(
            {
                "date": current.isoformat(),
                "weekday": current.strftime("%A"),
                "tasks": serialize_items(ordered, task_lookup, today),
            }
        )
        current += timedelta(days=1)

    return JsonResponse(
        {
            "meta": build_meta(today, week_start, week_end),
            "days": days,
        }
    )


# -----------------------------------------------------------------------------
# Subjects / courses
# -----------------------------------------------------------------------------

def subjects_api(request):
    if request.method == "GET":
        today = timezone.localdate()
        subjects = [
            subject_payload(subject, today)
            for subject in Subject.objects.filter(owner=request.user).prefetch_related("tasks", "assessments")
        ]
        return JsonResponse({"subjects": subjects})

    if request.method == "POST":
        try:
            payload = read_json_body(request)
            use_template = payload.pop("with_default_assessments", False) is True
            validate_allowed_fields(payload, SUBJECT_INPUT_FIELDS)
            merged = {
                "name": "",
                "code": "",
                "semester": "",
                "color": "lavender",
            }
            merged.update(payload)
            data = normalize_subject_data(merged)
            with transaction.atomic():
                subject = apply_subject_data(Subject(owner=request.user), data)
                if use_template:
                    for row in default_assessments():
                        apply_assessment_data(
                            Assessment(),
                            normalize_assessment_data({**row, "subject_id": subject.id, "score": None}),
                            subject,
                        )
        except PlanitValidationError as error:
            return validation_response(error)

        return JsonResponse(
            {"subject": subject_payload(subject, timezone.localdate())},
            status=201,
        )

    return method_not_allowed("GET", "POST")


def subject_detail_api(request, subject_id):
    try:
        subject = get_subject(request.user, subject_id)
    except PlanitValidationError as error:
        return validation_response(error)

    if request.method == "GET":
        return JsonResponse(
            {"subject": subject_payload(subject, timezone.localdate(), include_detail=True)}
        )

    if request.method == "PATCH":
        try:
            payload = read_json_body(request)
            validate_allowed_fields(payload, SUBJECT_INPUT_FIELDS)
            merged = subject_input_data(subject)
            merged.update(payload)
            data = normalize_subject_data(merged)
            apply_subject_data(subject, data)
        except PlanitValidationError as error:
            return validation_response(error)

        return JsonResponse(
            {"subject": subject_payload(subject, timezone.localdate(), include_detail=True)}
        )

    if request.method == "DELETE":
        subject.delete()
        return HttpResponse(status=204)

    return method_not_allowed("GET", "PATCH", "DELETE")


def subject_grade_api(request, subject_id):
    if request.method != "GET":
        return method_not_allowed("GET")

    try:
        subject = get_subject(request.user, subject_id)
        target = normalize_target(request.GET.get("target", "80"))
        overview = grade_overview(list(subject.assessments.all()), target)
    except (PlanitValidationError, ValueError) as error:
        if isinstance(error, PlanitValidationError):
            return validation_response(error)
        return api_error("grade_error", str(error), status=400)

    return JsonResponse(
        {
            "subject": serialize_subject(subject),
            "grade": overview,
        }
    )


# -----------------------------------------------------------------------------
# Assessments
# -----------------------------------------------------------------------------

def assessments_api(request):
    if request.method != "POST":
        return method_not_allowed("POST")

    try:
        payload = read_json_body(request)
        validate_allowed_fields(payload, ASSESSMENT_INPUT_FIELDS)
        data = normalize_assessment_data(payload)
        subject = get_subject(request.user, data["subject_id"])
        validate_assessment_total(subject.id, data["weight"])
        assessment = apply_assessment_data(Assessment(), data, subject)
    except PlanitValidationError as error:
        return validation_response(error)

    return JsonResponse(
        {"assessment": serialize_assessment(assessment)},
        status=201,
    )


def assessment_detail_api(request, assessment_id):
    try:
        assessment = get_assessment(request.user, assessment_id)
    except PlanitValidationError as error:
        return validation_response(error)

    if request.method == "PATCH":
        try:
            payload = read_json_body(request)
            validate_allowed_fields(payload, ASSESSMENT_INPUT_FIELDS)
            merged = assessment_input_data(assessment)
            merged.update(payload)
            data = normalize_assessment_data(merged)
            subject = get_subject(request.user, data["subject_id"])
            validate_assessment_total(
                subject.id,
                data["weight"],
                assessment_id=assessment.id,
            )
            apply_assessment_data(assessment, data, subject)
        except PlanitValidationError as error:
            return validation_response(error)

        return JsonResponse(
            {"assessment": serialize_assessment(assessment)}
        )

    if request.method == "DELETE":
        assessment.delete()
        return HttpResponse(status=204)

    return method_not_allowed("PATCH", "DELETE")


# -----------------------------------------------------------------------------
# Projects
# -----------------------------------------------------------------------------

def projects_api(request):
    if request.method == "GET":
        today = timezone.localdate()
        projects = [
            project_payload(project, today)
            for project in Project.objects.filter(owner=request.user).select_related("subject").prefetch_related("tasks")
        ]
        return JsonResponse({"projects": projects})

    if request.method == "POST":
        try:
            payload = read_json_body(request)
            validate_allowed_fields(payload, PROJECT_INPUT_FIELDS)
            merged = {
                "title": "",
                "description": "",
                "due_date": None,
                "subject_id": None,
            }
            merged.update(payload)
            data = normalize_project_data(merged)
            subject = get_subject(request.user, data["subject_id"]) if data["subject_id"] else None
            project = apply_project_data(Project(owner=request.user), data, subject)
        except PlanitValidationError as error:
            return validation_response(error)

        return JsonResponse(
            {"project": project_payload(project, timezone.localdate(), include_detail=True)},
            status=201,
        )

    return method_not_allowed("GET", "POST")


def project_detail_api(request, project_id):
    try:
        project = get_project(request.user, project_id)
    except PlanitValidationError as error:
        return validation_response(error)

    if request.method == "GET":
        return JsonResponse(
            {"project": project_payload(project, timezone.localdate(), include_detail=True)}
        )

    if request.method == "PATCH":
        try:
            payload = read_json_body(request)
            validate_allowed_fields(payload, PROJECT_INPUT_FIELDS)
            merged = project_input_data(project)
            merged.update(payload)
            data = normalize_project_data(merged)
            new_subject = get_subject(request.user, data["subject_id"]) if data["subject_id"] else None

            if project.subject_id != data["subject_id"] and new_subject is not None:
                conflicts = project.tasks.exclude(subject__isnull=True).exclude(subject=new_subject)
                if conflicts.exists():
                    raise PlanitValidationError(
                        "Some project tasks belong to a different subject. Update those tasks first.",
                        code="project_subject_conflict",
                        field="subject_id",
                    )

            with transaction.atomic():
                apply_project_data(project, data, new_subject)
                if new_subject is not None:
                    project.tasks.filter(subject__isnull=True).update(subject=new_subject)
        except PlanitValidationError as error:
            return validation_response(error)

        return JsonResponse(
            {"project": project_payload(project, timezone.localdate(), include_detail=True)}
        )

    if request.method == "DELETE":
        project.delete()
        return HttpResponse(status=204)

    return method_not_allowed("GET", "PATCH", "DELETE")


def _user_settings(user):
    from .views_extra import get_user_settings
    return get_user_settings(user)
