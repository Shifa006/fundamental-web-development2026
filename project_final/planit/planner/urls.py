from django.urls import path

from . import views


urlpatterns = [
    # Pages
    path(
        "",
        views.today_page,
        name="today",
    ),

    path(
        "tasks/",
        views.tasks_page,
        name="tasks",
    ),

    path(
        "courses/",
        views.courses_page,
        name="courses",
    ),

    path(
        "projects/",
        views.projects_page,
        name="projects",
    ),

    # APIs
    path(
        "api/tasks/",
        views.tasks_api,
        name="api_tasks",
    ),

    path(
        "api/today/",
        views.today_api,
        name="api_today",
    ),

    path(
        "api/week/",
        views.week_api,
        name="api_week",
    ),
]

path(
    "api/tasks/<int:task_id>/",
    views.task_detail_api,
    name="api_task_detail",
),

path(
    "api/task-options/",
    views.task_options_api,
    name="api_task_options",
),