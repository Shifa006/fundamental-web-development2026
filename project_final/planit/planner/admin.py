from django.contrib import admin

from .models import (
    Assessment,
    Project,
    Subject,
    Task,
)


admin.site.register(Subject)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Assessment)