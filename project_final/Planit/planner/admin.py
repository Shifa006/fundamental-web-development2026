from django.contrib import admin

from .models import Assessment, Project, Subject, Task


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "semester", "color")
    search_fields = ("name", "code", "semester")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "due_date")
    list_filter = ("subject",)
    search_fields = ("title", "description")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "area",
        "kind",
        "priority",
        "due_date",
        "completed",
        "subject",
        "project",
    )
    list_filter = ("area", "kind", "priority", "completed", "subject")
    search_fields = ("title", "description")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "weight", "score", "max_score")
    list_filter = ("subject",)
    search_fields = ("name",)
