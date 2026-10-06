# Release Manifest — Planit Presentation-Ready v4

## Application

- Django 6.1.2 project configuration
- SQLite migrations 0001–0003
- Django session login/logout
- authentication middleware for pages and APIs
- Tasks CRUD + Today + This Week + Exam Mode
- Courses + Assessments + Grade target calculator
- Projects + derived progress
- Python Functions/HOF and OOP domain layer
- Mint Day / Night Quest theme mode
- Top Focus task ranking
- local Bootstrap 5.3.6
- responsive Pastel Quest UI

## Presentation documentation

- `README.md`
- `FINAL_SETUP.md`
- `docs/PRESENTATION_READY_V4.md`
- `docs/TEACHER_QA_CHEATSHEET.md`
- `docs/CODE_LOCATION_MAP.md`
- `docs/RUNSERVER_FLOW.md`
- `docs/ARCHITECTURE.md`
- `docs/PRESENTATION_GUIDE.md`
- `docs/ACADEMIC_ARTICLE_DRAFT.md`
- `docs/TEST_REPORT.md`
- `docs/FINAL_CHECKLIST.md`

## Intentionally excluded

- `.venv/`
- `db.sqlite3`
- local superuser accounts
- Python caches
- macOS metadata

## Verified release result

```text
python manage.py check
=> no issues

python manage.py makemigrations --check --dry-run
=> no changes detected

python manage.py test planner.tests
=> 64 tests passed
```
