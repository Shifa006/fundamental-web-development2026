from django.urls import path

from . import views

urlpatterns = [
    # Pages
    path("", views.today_page, name="today"),
    path("tasks/", views.tasks_page, name="tasks"),
    path("courses/", views.courses_page, name="courses"),
    path("projects/", views.projects_page, name="projects"),

    # Tasks / planner APIs
    path("api/tasks/", views.tasks_api, name="api_tasks"),
    path("api/tasks/<int:task_id>/", views.task_detail_api, name="api_task_detail"),
    path("api/task-options/", views.task_options_api, name="api_task_options"),
    path("api/today/", views.today_api, name="api_today"),
    path("api/week/", views.week_api, name="api_week"),

    # Course APIs
    path("api/subjects/", views.subjects_api, name="api_subjects"),
    path("api/subjects/<int:subject_id>/", views.subject_detail_api, name="api_subject_detail"),
    path("api/subjects/<int:subject_id>/grade/", views.subject_grade_api, name="api_subject_grade"),

    # Assessment APIs
    path("api/assessments/", views.assessments_api, name="api_assessments"),
    path("api/assessments/<int:assessment_id>/", views.assessment_detail_api, name="api_assessment_detail"),

    # Project APIs
    path("api/projects/", views.projects_api, name="api_projects"),
    path("api/projects/<int:project_id>/", views.project_detail_api, name="api_project_detail"),
]
