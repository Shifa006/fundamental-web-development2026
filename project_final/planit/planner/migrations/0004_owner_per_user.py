import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_existing_rows(apps, schema_editor):
    """Give pre-v5 rows to the first account so nothing is orphaned."""
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    owner = User.objects.order_by("id").first()
    if owner is None:
        return
    for name in ("Subject", "Project", "Task"):
        apps.get_model("planner", name).objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("planner", "0003_alter_project_description_alter_task_description_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="subject", name="uniq_subject_name_semester"),
        migrations.AddField(
            model_name="subject",
            name="owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="planit_%(class)ss", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="project",
            name="owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="planit_%(class)ss", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="task",
            name="owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="planit_%(class)ss", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name="subject",
            constraint=models.UniqueConstraint(fields=("owner", "name", "semester"), name="uniq_subject_name_semester"),
        ),
        migrations.RunPython(assign_existing_rows, migrations.RunPython.noop),
    ]
