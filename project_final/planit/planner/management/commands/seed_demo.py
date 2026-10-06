from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from planner.models import Assessment, Project, Subject, Task


class Command(BaseCommand):
    help = "Create date-relative demo data for the Planit presentation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing Planit data before creating demo data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Assessment.objects.all().delete()
            Task.objects.all().delete()
            Project.objects.all().delete()
            Subject.objects.all().delete()

        today = timezone.localdate()

        web, _ = Subject.objects.update_or_create(
            name="Web Development",
            semester="1/2026",
            defaults={"code": "WEB101", "color": "butter"},
        )
        python, _ = Subject.objects.update_or_create(
            name="Python Programming",
            semester="1/2026",
            defaults={"code": "PY101", "color": "lavender"},
        )
        calculus, _ = Subject.objects.update_or_create(
            name="Calculus",
            semester="1/2026",
            defaults={"code": "MATH101", "color": "sage"},
        )
        physics, _ = Subject.objects.update_or_create(
            name="Physics",
            semester="1/2026",
            defaults={"code": "PHY101", "color": "clay"},
        )

        planit, _ = Project.objects.update_or_create(
            title="Planit Final Project",
            defaults={
                "description": "Combined final project for Web Development and Python Functions & OOP.",
                "subject": web,
                "due_date": today + timedelta(days=24),
            },
        )

        Assessment.objects.update_or_create(
            subject=web,
            name="Assignment",
            defaults={"weight": 20, "max_score": 20, "score": 18},
        )
        Assessment.objects.update_or_create(
            subject=web,
            name="Midterm",
            defaults={"weight": 30, "max_score": 30, "score": 24},
        )
        Assessment.objects.update_or_create(
            subject=web,
            name="Project",
            defaults={"weight": 20, "max_score": 20, "score": None},
        )
        Assessment.objects.update_or_create(
            subject=web,
            name="Final",
            defaults={"weight": 30, "max_score": 30, "score": None},
        )

        demo_tasks = [
            {
                "title": "Prepare Python presentation",
                "area": "academic",
                "kind": "study",
                "priority": "urgent",
                "due_date": today,
                "completed": False,
                "subject": python,
                "project": None,
            },
            {
                "title": "Refine Planit interface",
                "area": "academic",
                "kind": "assignment",
                "priority": "normal",
                "due_date": today,
                "completed": True,
                "subject": web,
                "project": planit,
            },
            {
                "title": "Finish API tests",
                "area": "academic",
                "kind": "assignment",
                "priority": "urgent",
                "due_date": today - timedelta(days=2),
                "completed": False,
                "subject": web,
                "project": planit,
            },
            {
                "title": "Calculus midterm",
                "area": "academic",
                "kind": "exam",
                "priority": "urgent",
                "due_date": today + timedelta(days=3),
                "completed": False,
                "subject": calculus,
                "project": None,
            },
            {
                "title": "Physics quiz",
                "area": "academic",
                "kind": "exam",
                "priority": "normal",
                "due_date": today - timedelta(days=1),
                "completed": False,
                "subject": physics,
                "project": None,
            },
            {
                "title": "Review DOM lecture",
                "area": "academic",
                "kind": "study",
                "priority": "normal",
                "due_date": today + timedelta(days=2),
                "completed": False,
                "subject": web,
                "project": None,
            },
            {
                "title": "Write report introduction",
                "area": "academic",
                "kind": "general",
                "priority": "normal",
                "due_date": None,
                "completed": False,
                "subject": web,
                "project": planit,
            },
            {
                "title": "Buy groceries",
                "area": "personal",
                "kind": "general",
                "priority": "urgent",
                "due_date": today,
                "completed": False,
                "subject": None,
                "project": None,
            },
            {
                "title": "Organize desk",
                "area": "personal",
                "kind": "general",
                "priority": "later",
                "due_date": today + timedelta(days=5),
                "completed": False,
                "subject": None,
                "project": None,
            },
        ]

        for data in demo_tasks:
            title = data.pop("title")
            Task.objects.update_or_create(
                title=title,
                defaults=data,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Planit demo data is ready for {today.isoformat()}."
            )
        )
