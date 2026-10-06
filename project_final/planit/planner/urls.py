from django.urls import path

from . import views


urlpatterns = [
    path("", views.today_page, name="today"),
    path("tasks/", views.tasks_page, name="tasks"),
    path("courses/", views.courses_page, name="courses"),
    path("projects/", views.projects_page, name="projects"),
]