# Planit

Planit is a responsive authenticated student planner built as a combined final project for **Fundamental Web Development** and **Python (Functions & OOP)**.

It connects a Django/SQLite backend to a dynamic JavaScript interface using JSON APIs, Fetch API, async/await, DOM rendering, CSRF-protected CRUD, reusable functions, and an object-oriented Python domain layer.

## Core features

- Django login/logout with session authentication and wrong-password feedback
- Today dashboard with progress, overdue work, Top Focus, next exam, area filters, and Exam Mode
- Tasks with CRUD, search, filters, sorting, All Tasks, and This Week
- Exam Mode persisted with `localStorage`
- Mint Day / Night Quest visual theme persisted with `localStorage`
- Courses with CRUD and linked task summaries
- Assessments with CRUD and server-side validation
- Grade target calculator (canonical example: target 80% -> required remaining average 76%)
- Projects with CRUD, linked tasks, and derived progress
- Responsive pastel quest/game UI with mint, sage, lavender, butter, and peach accents
- Local Bootstrap bundle so core UI works without internet
- Loading, empty, error, and toast states
- Demo-data command and automated tests

## Technology

- Python 3.14
- Django 6.1.2
- SQLite
- HTML5 / CSS3
- Bootstrap 5.3.6 (bundled locally)
- Vanilla JavaScript
- Fetch API / async-await / JSON / DOM / Web Storage

The interface uses a local/system font stack and bundled Bootstrap, so the core UI has no remote font or framework dependency.

## Quick start (fresh database)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --reset --demo-user
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Demo login after the seed command:

```text
username: student
password: PlanitDemo123!
```

Optional admin account:

```bash
python manage.py createsuperuser
```

Then open `http://127.0.0.1:8000/admin/`.

## If you already have your previous Planit database

This release intentionally does **not** include `db.sqlite3`. To keep your existing data:

1. Copy your existing `db.sqlite3` into the project root, next to `manage.py`.
2. Activate your virtual environment.
3. Run:

```bash
python manage.py migrate
python manage.py check
python manage.py test planner.tests -v 2
```

Migration `0003` adds validation-aligned database constraints. It was checked against the database supplied with the previous Planit ZIP.

## Important: do not run `makemigrations` during normal setup

The required migrations are already included:

```text
planner/migrations/0001_initial.py
planner/migrations/0002_...
planner/migrations/0003_...
```

Use `python manage.py migrate`. Run `makemigrations` only after intentionally changing Django models.

## Validation layers

Planit validates critical data at more than one level:

```text
Browser UX rules
      ↓
JSON/API validators
      ↓
Django model validation
      ↓
Database check constraints
```

Examples include:

- personal tasks must be `general` and cannot link to academic subjects/projects
- exams require a due date
- a task subject must match its project's subject
- assessment weight must be > 0 and <= 100
- score must be between 0 and max score
- configured assessment weight for a subject cannot exceed 100

## Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test planner.tests -v 2
```

See `docs/TEST_REPORT.md` and `docs/UI_REDESIGN_V3.md` for verification and the current visual system.

## Project structure

```text
planit/
├── config/                     Django project settings
├── planner/
│   ├── domain.py               OOP domain rules
│   ├── services.py             reusable functions / HOF / calculations
│   ├── validators.py           API normalization and validation
│   ├── models.py               persistence + model invariants
│   ├── views.py                page views + JSON APIs
│   ├── urls.py                 routes
│   ├── management/commands/    seed_demo command
│   ├── migrations/             database schema history
│   ├── static/                 CSS, JS, local Bootstrap
│   ├── templates/              page and modal templates
│   └── tests/                  automated tests
├── docs/                       report/presentation material
├── screenshots/                screenshot checklist
├── manage.py
└── requirements.txt
```

## Architecture in one line

```text
Browser -> Fetch/JSON -> Django API -> validators/services/domain -> ORM -> SQLite
        <- DOM rendering <- JSON response <- derived business rules <-
```

## Scope

Planit V1 is intentionally an **authenticated local prototype**. It has login/logout and protected APIs, but it does not implement public registration, per-user data ownership, password-reset email, push notifications, PWA/offline data sync, or external calendar integration.

## Final-project documentation

Start with:

- `FINAL_SETUP.md`
- `docs/PHASE_MAP.md`
- `docs/ARCHITECTURE.md`
- `docs/ACADEMIC_ARTICLE_DRAFT.md`
- `docs/PRESENTATION_GUIDE.md`
- `docs/PRESENTATION_READY_V4.md`
- `docs/TEACHER_QA_CHEATSHEET.md`
- `docs/CODE_LOCATION_MAP.md`
- `docs/RUNSERVER_FLOW.md`
- `docs/FINAL_CHECKLIST.md`
- `screenshots/README.md`

## Quick start (v1.3)
```
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --demo-user              # login: student / PlanitDemo123!
python manage.py runserver
python manage.py test                               # 95 tests
```
Sign-up is at /signup/. See docs/CHANGELOG_V5.md for what changed.
