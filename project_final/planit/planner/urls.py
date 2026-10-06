from django.urls import path

from . import views, views_extra

urlpatterns = [
    # Authentication
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("logout/", views.logout_page, name="logout"),

    # Pages
    path("", views.today_page, name="today"),
    path("tasks/", views.tasks_page, name="tasks"),
    path("courses/", views.courses_page, name="courses"),
    path("projects/", views.projects_page, name="projects"),

    # Tasks / planner APIs
    path("api/tasks/", views.tasks_api, name="api_tasks"),
    path("api/tasks/<int:task_id>/", views.task_detail_api, name="api_task_detail"),
    path("api/tasks/<int:task_id>/duplicate/", views.task_duplicate_api, name="api_task_duplicate"),
    path("api/month/", views_extra.month_api, name="api_month"),
    path("api/settings/", views_extra.settings_api, name="api_settings"),
    path("api/modules/", views_extra.modules_api, name="api_modules"),
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
