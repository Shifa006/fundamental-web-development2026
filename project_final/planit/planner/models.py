from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Subject(models.Model):
    COLOR_CHOICES = [
        ("lavender", "Lavender"),
        ("butter", "Butter"),
        ("sage", "Sage"),
        ("clay", "Clay"),
    ]

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, blank=True)
    semester = models.CharField(max_length=50, blank=True)
    color = models.CharField(
        max_length=16,
        choices=COLOR_CHOICES,
        default="lavender",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="planit_%(class)ss",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name", "semester"],
                name="uniq_subject_name_semester",
            )
        ]

    def clean(self):
        self.name = (self.name or "").strip()
        self.code = (self.code or "").strip()
        self.semester = (self.semester or "").strip()

        if not self.name:
            raise ValidationError({"name": "Course name is required."})

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=2000)
    due_date = models.DateField(null=True, blank=True)
    subject = models.ForeignKey(
        Subject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="planit_%(class)ss",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "title", "id"]

    def clean(self):
        self.title = (self.title or "").strip()
        self.description = (self.description or "").strip()

        if not self.title:
            raise ValidationError({"title": "Project title is required."})

        # If an existing project is assigned to a subject, linked tasks that
        # already have another subject would become inconsistent.
        if self.pk and self.subject_id:
            conflict_exists = self.tasks.exclude(subject__isnull=True).exclude(
                subject_id=self.subject_id
            ).exists()
            if conflict_exists:
                raise ValidationError(
                    {
                        "subject": (
                            "Some project tasks belong to a different subject. "
                            "Update those tasks first."
                        )
                    }
                )

    def __str__(self):
        return self.title


class Task(models.Model):
    AREA_CHOICES = [
        ("academic", "Academic"),
        ("personal", "Personal"),
    ]

    KIND_CHOICES = [
        ("general", "General"),
        ("assignment", "Assignment"),
        ("study", "Study"),
        ("exam", "Exam"),
    ]

    PRIORITY_CHOICES = [
        ("urgent", "Urgent"),
        ("normal", "Normal"),
        ("later", "Later"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=2000)
    area = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        default="academic",
    )
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        default="general",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
    )
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    subject = models.ForeignKey(
        Subject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="planit_%(class)ss",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["completed", "due_date", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~models.Q(area="personal")
                    | (
                        models.Q(kind="general")
                        & models.Q(subject__isnull=True)
                        & models.Q(project__isnull=True)
                    )
                ),
                name="task_personal_general_unlinked",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(kind="exam")
                    | models.Q(due_date__isnull=False)
                ),
                name="task_exam_requires_due_date",
            ),
        ]

    def clean(self):
        self.title = (self.title or "").strip()
        self.description = (self.description or "").strip()

        errors = {}

        if not self.title:
            errors["title"] = "Task title is required."

        if self.area == "personal":
            if self.kind != "general":
                errors["kind"] = "Personal tasks must use the general type."
            if self.subject_id is not None:
                errors["subject"] = "Personal tasks cannot belong to a subject."
            if self.project_id is not None:
                errors["project"] = "Personal tasks cannot belong to a project."

        if self.kind == "exam" and self.due_date is None:
            errors["due_date"] = "An exam must have a due date."

        if self.project_id is not None:
            project_subject_id = self.project.subject_id

            if project_subject_id is not None:
                if self.subject_id is None:
                    # Keep the same normalization rule used by the API: a task
                    # inherits the project's subject when it has not selected one.
                    self.subject = self.project.subject
                elif self.subject_id != project_subject_id:
                    errors["subject"] = "Task subject must match the project subject."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class Assessment(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    name = models.CharField(max_length=120)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=8, decimal_places=2)
    score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(weight__gt=0, weight__lte=100),
                name="assessment_weight_0_100",
            ),
            models.CheckConstraint(
                condition=models.Q(max_score__gt=0),
                name="assessment_max_score_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(score__isnull=True)
                    | (
                        models.Q(score__gte=0)
                        & models.Q(score__lte=models.F("max_score"))
                    )
                ),
                name="assessment_score_valid",
            ),
        ]

    def clean(self):
        self.name = (self.name or "").strip()
        errors = {}

        if not self.name:
            errors["name"] = "Assessment name is required."

        if self.weight is not None and not (
            Decimal("0") < self.weight <= Decimal("100")
        ):
            errors["weight"] = "Weight must be greater than 0 and at most 100."

        if self.max_score is not None and self.max_score <= 0:
            errors["max_score"] = "Maximum score must be greater than 0."

        if self.score is not None and self.max_score is not None:
            if self.score < 0 or self.score > self.max_score:
                errors["score"] = "Score must be between 0 and the maximum score."

        if self.subject_id and self.weight is not None:
            others = type(self).objects.filter(subject_id=self.subject_id)
            if self.pk:
                others = others.exclude(pk=self.pk)

            configured = sum(
                (assessment.weight for assessment in others),
                Decimal("0"),
            )

            if configured + self.weight > Decimal("100"):
                available = Decimal("100") - configured
                errors["weight"] = (
                    "Total assessment weight cannot exceed 100. "
                    f"Available weight: {available}."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class UserSettings(models.Model):
    """Per-user preferences: enabled modules and "remember last used" defaults."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="planit_settings",
    )
    enabled_modules = models.JSONField(default=list, blank=True)
    onboarding_done = models.BooleanField(default=False)
    last_area = models.CharField(max_length=16, default="academic")
    last_kind = models.CharField(max_length=16, default="assignment")
    last_priority = models.CharField(max_length=16, default="normal")
    last_subject = models.ForeignKey(
        Subject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def __str__(self):
        return f"Settings for {self.user}"
