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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "semester"],
                name="uniq_subject_name_semester",
            )
        ]

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    subject = models.ForeignKey(
        Subject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "title", "id"]

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
    description = models.TextField(blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["completed", "due_date", "id"]

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

    def __str__(self):
        return f"{self.subject.name} - {self.name}"
