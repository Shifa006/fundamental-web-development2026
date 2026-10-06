from datetime import date


VALID_AREAS = {
    "academic",
    "personal",
}

VALID_KINDS = {
    "general",
    "assignment",
    "study",
    "exam",
}

VALID_PRIORITIES = {
    "urgent",
    "normal",
    "later",
}

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


class TaskValidationError(ValueError):

    def __init__(
        self,
        message,
        *,
        code="invalid_task",
        field=None,
        status=400,
    ):
        super().__init__(message)

        self.code = code
        self.field = field
        self.status = status


def validate_allowed_fields(data):
    unknown = (
        set(data)
        - TASK_INPUT_FIELDS
    )

    if unknown:
        field = sorted(unknown)[0]

        raise TaskValidationError(
            f"Unknown field: {field}.",
            code="unknown_field",
            field=field,
        )


def parse_optional_id(
    value,
    field_name,
):
    if value in (
        None,
        "",
    ):
        return None

    if isinstance(value, bool):
        raise TaskValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    try:
        value = int(value)
    except (
        TypeError,
        ValueError,
    ):
        raise TaskValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    if value <= 0:
        raise TaskValidationError(
            f"{field_name} must be a valid ID.",
            field=field_name,
        )

    return value


def parse_due_date(value):
    if value in (
        None,
        "",
    ):
        return None

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(
            str(value)
        )
    except ValueError:
        raise TaskValidationError(
            "Due date must use YYYY-MM-DD format.",
            code="invalid_date",
            field="due_date",
        )


def normalize_task_data(data):
    title = str(
        data.get(
            "title",
            "",
        )
    ).strip()

    if not title:
        raise TaskValidationError(
            "Task title is required.",
            code="required",
            field="title",
        )

    if len(title) > 200:
        raise TaskValidationError(
            "Task title cannot exceed 200 characters.",
            field="title",
        )


    description_value = data.get(
        "description",
        "",
    )

    description = (
        ""
        if description_value is None
        else str(description_value).strip()
    )


    area = data.get(
        "area",
        "academic",
    )

    if area not in VALID_AREAS:
        raise TaskValidationError(
            "Area must be academic or personal.",
            field="area",
        )


    kind = data.get(
        "kind",
        "general",
    )

    if kind not in VALID_KINDS:
        raise TaskValidationError(
            "Invalid task type.",
            field="kind",
        )


    priority = data.get(
        "priority",
        "normal",
    )

    if priority not in VALID_PRIORITIES:
        raise TaskValidationError(
            "Invalid task priority.",
            field="priority",
        )


    completed = data.get(
        "completed",
        False,
    )

    if not isinstance(
        completed,
        bool,
    ):
        raise TaskValidationError(
            "Completed must be true or false.",
            field="completed",
        )


    due_date = parse_due_date(
        data.get("due_date")
    )

    subject_id = parse_optional_id(
        data.get("subject_id"),
        "subject_id",
    )

    project_id = parse_optional_id(
        data.get("project_id"),
        "project_id",
    )


    if (
        area == "personal"
        and kind != "general"
    ):
        raise TaskValidationError(
            "Personal tasks must use the general type.",
            code="invalid_area_kind",
            field="kind",
        )


    if (
        kind == "exam"
        and due_date is None
    ):
        raise TaskValidationError(
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