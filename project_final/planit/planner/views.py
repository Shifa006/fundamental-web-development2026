from django.shortcuts import render


def today_page(request):
    return render(request, "planner/today.html")


def tasks_page(request):
    return render(request, "planner/tasks.html")


def courses_page(request):
    return render(request, "planner/courses.html")


def projects_page(request):
    return render(request, "planner/projects.html")