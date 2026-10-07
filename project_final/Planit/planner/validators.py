from datetime import date
from decimal import Decimal, InvalidOperation


VALID_AREAS = {"academic", "personal"}
VALID_KINDS = {"general", "assignment", "study", "exam"}
VALID_PRIORITIES = {"urgent", "normal", "later"}
VALID_COLORS = {"lavender", "butter", "sage", "clay"}

TASK_INPUT_FIELDS = {
    "title",
    "description",
    "area",
    "kind",
    "priority",
    "due_date",
    "completed",
    "subject_id",
    "project_id",
}

SUBJECT_INPUT_FIELDS = {
    "name",
    "code",
    "semester",
    "color",
}

PROJECT_INPUT_FIELDS = {
    "title",
    "description",
    "due_date",
    "subject_id",
}

ASSESSMENT_INPUT_FIELDS = {
    "subject_id",
    "name",
    "weight",
    "max_score",
    "score",
}


class PlanitValidationError(ValueError):
    def __init__(
        self,
        message,
        *,
        code="validation_error",
        field=None,
        status=400,
    ):
        super().__init__(message)
        self.code = code
        self.field = field
        self.status = status


def validate_allowed_fields(data, allowed_fields):
    unknown = set(data) - set(allowed_fields)

    if unknown:
        field = sorted(unknown)[0]
        raise PlanitValidationError(
            f"Unknown field: {field}.",
            code="unknown_field",
            field=field,
        )


def parse_optional_id(value, field_name):
    if value in {None, ""}:
        return None

    if isinstance(value, bool):
        raise PlanitValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    try:
        value = int(value)
    except (TypeError, ValueError):
        raise PlanitValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    if value <= 0:
        raise PlanitValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    return value


def parse_due_date(value, field_name="due_date"):
    if value in {None, ""}:
        return None

    if isinstance(value, date):
        return value

    try:
        parsed = date.fromisoformat(str(value))
    except ValueError:
        raise PlanitValidationError(
            "Due date must use YYYY-MM-DD format.",
            code="invalid_date",
            field=field_name,
        )
    else:
        # try/except/else: this branch runs only when parsing succeeded.
        return parsed


def parse_decimal(value, field_name, *, optional=False):
    if value in {None, ""}:
        if optional:
            return None
        raise PlanitValidationError(
            f"{field_name} is required.",
            code="required",
            field=field_name,
        )

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise PlanitValidationError(
            f"{field_name} must be a number.",
            field=field_name,
        )

    if not number.is_finite():
        raise PlanitValidationError(
            f"{field_name} must be a finite number.",
            field=field_name,
        )

    if number.as_tuple().exponent < -2:
        raise PlanitValidationError(
            f"{field_name} can have at most two decimal places.",
            field=field_name,
        )

    return number


def normalize_task_data(data):
    title = str(data.get("title", "")).strip()

    if not title:
        raise PlanitValidationError(
            "Task title is required.",
            code="required",
            field="title",
        )

    if len(title) > 200:
        raise PlanitValidationError(
            "Task title cannot exceed 200 characters.",
            field="title",
        )

    description_value = data.get("description", "")
    description = "" if description_value is None else str(description_value).strip()

    if len(description) > 2000:
        raise PlanitValidationError(
            "Description cannot exceed 2000 characters.",
            field="description",
        )

    area = data.get("area", "academic")
    kind = data.get("kind", "general")
    priority = data.get("priority", "normal")
    completed = data.get("completed", False)

    if area not in VALID_AREAS:
        raise PlanitValidationError(
            "Area must be academic or personal.",
            field="area",
        )

    if kind not in VALID_KINDS:
        raise PlanitValidationError("Invalid task type.", field="kind")

    if priority not in VALID_PRIORITIES:
        raise PlanitValidationError("Invalid task priority.", field="priority")

    if not isinstance(completed, bool):
        raise PlanitValidationError(
            "Completed must be true or false.",
            field="completed",
        )

    due_date = parse_due_date(data.get("due_date"))
    subject_id = parse_optional_id(data.get("subject_id"), "subject_id")
    project_id = parse_optional_id(data.get("project_id"), "project_id")

    if area == "personal":
        if kind != "general":
            raise PlanitValidationError(
                "Personal tasks must use the general type.",
                code="invalid_area_kind",
                field="kind",
            )

        if subject_id is not None:
            raise PlanitValidationError(
                "Personal tasks cannot belong to a subject.",
                code="personal_subject_not_allowed",
                field="subject_id",
            )

        if project_id is not None:
            raise PlanitValidationError(
                "Personal tasks cannot belong to a project.",
                code="personal_project_not_allowed",
                field="project_id",
            )

    if kind == "exam" and due_date is None:
        raise PlanitValidationError(
            "An exam must have a due date.",
            code="exam_date_required",
            field="due_date",
        )

    return {
        "title": title,
        "description": description,
        "area": area,
        "kind": kind,
        "priority": priority,
        "due_date": due_date,
        "completed": completed,
        "subject_id": subject_id,
        "project_id": project_id,
    }


def normalize_subject_data(data):
    name = str(data.get("name", "")).strip()
    code = str(data.get("code", "") or "").strip()
    semester = str(data.get("semester", "") or "").strip()
    color = data.get("color", "lavender")

    if not name:
        raise PlanitValidationError(
            "Course name is required.",
            code="required",
            field="name",
        )

    if len(name) > 120:
        raise PlanitValidationError("Course name is too long.", field="name")
    if len(code) > 20:
        raise PlanitValidationError("Course code is too long.", field="code")
    if len(semester) > 50:
        raise PlanitValidationError("Semester is too long.", field="semester")
    if color not in VALID_COLORS:
        raise PlanitValidationError("Invalid course color.", field="color")

    return {
        "name": name,
        "code": code,
        "semester": semester,
        "color": color,
    }


def normalize_project_data(data):
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "") or "").strip()

    if not title:
        raise PlanitValidationError(
            "Project title is required.",
            code="required",
            field="title",
        )

    if len(title) > 200:
        raise PlanitValidationError("Project title is too long.", field="title")

    if len(description) > 2000:
        raise PlanitValidationError(
            "Project description cannot exceed 2000 characters.",
            field="description",
        )

    return {
        "title": title,
        "description": description,
        "due_date": parse_due_date(data.get("due_date")),
        "subject_id": parse_optional_id(data.get("subject_id"), "subject_id"),
    }


def normalize_assessment_data(data):
    name = str(data.get("name", "")).strip()

    if not name:
        raise PlanitValidationError(
            "Assessment name is required.",
            code="required",
            field="name",
        )

    if len(name) > 120:
        raise PlanitValidationError("Assessment name is too long.", field="name")

    subject_id = parse_optional_id(data.get("subject_id"), "subject_id")

    if subject_id is None:
        raise PlanitValidationError(
            "Subject is required.",
            code="required",
            field="subject_id",
        )

    weight = parse_decimal(data.get("weight"), "weight")
    max_score = parse_decimal(data.get("max_score"), "max_score")
    score = parse_decimal(data.get("score"), "score", optional=True)

    if not Decimal("0") < weight <= Decimal("100"):
        raise PlanitValidationError(
            "Weight must be greater than 0 and at most 100.",
            field="weight",
        )

    if max_score <= 0:
        raise PlanitValidationError(
            "Maximum score must be greater than 0.",
            field="max_score",
        )

    if score is not None and not Decimal("0") <= score <= max_score:
        raise PlanitValidationError(
            "Score must be between 0 and the maximum score.",
            field="score",
        )

    return {
        "subject_id": subject_id,
        "name": name,
        "weight": weight,
        "max_score": max_score,
        "score": score,
    }


def normalize_target(value):
    target = parse_decimal(value, "target")

    if not Decimal("0") <= target <= Decimal("100"):
        raise PlanitValidationError(
            "Target must be between 0 and 100.",
            field="target",
        )

    return target
