# Planit Presentation-Ready v4 — Setup

This package is the clean source package. It deliberately excludes `.venv`, `db.sqlite3`, macOS metadata, caches, and user/admin credentials.

## Recommended installation

```bash
cd planit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test planner.tests -v 2
python manage.py seed_demo --reset --demo-user
python manage.py runserver
```

No `makemigrations` command is required.

## Keeping your current data

If you are replacing an older Planit code folder but want to preserve its data:

```text
old Planit/db.sqlite3
        ↓ copy
new Planit/db.sqlite3
```

Then run:

```bash
python manage.py migrate
python manage.py check
python manage.py test planner.tests -v 2
```

Do not copy the old `.venv` into this package. Create or reuse your own local virtual environment instead.

## Before demonstration

```bash
python manage.py seed_demo --reset --demo-user
python manage.py runserver
```

The seed command produces a predictable demo set using the current local date.

## Main URLs

```text
/login/      Login
/            Today (authentication required)
/tasks/      Tasks
/courses/    Courses
/projects/   Projects
/admin/      Django Admin (only after creating a superuser)
```

## If something fails

1. Confirm the virtual environment is active.
2. Run `python manage.py check`.
3. Run `python manage.py migrate`.
4. Run `python manage.py test planner.tests -v 2`.
5. Hard-refresh the browser if static files were recently replaced.
6. Check DevTools Console and Network > Fetch/XHR for the first failed request.

For a final hand-in ZIP, keep the repository clean: do not add `.venv`, `db.sqlite3`, `__pycache__`, `.DS_Store`, or `__MACOSX`.
