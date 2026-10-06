# Planit Presentation-Ready v4 — Test Report

This report records checks performed on the full presentation-ready release source.

## Automated Django checks

Commands:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test planner.tests -v 2
```

Final result:

```text
System check identified no issues.
No changes detected.
Found 64 tests.
Ran 64 tests.
OK
```

The suite includes domain/OOP rules, service functions, model constraints, CRUD APIs, grade calculation, project progress, CSRF, authentication, protected APIs, safe login redirects, semantic frontend hooks, local Bootstrap, and presentation UI contracts.

## Authentication verification

Verified behaviors:

- `/login/` is public
- unauthenticated `/` redirects to `/login/?next=/`
- unauthenticated `/api/tasks/` returns JSON HTTP `401`
- correct username/password creates a Django authenticated session
- wrong password displays an error and does not authenticate
- safe local `next` redirects are accepted
- external `next` URLs are ignored
- logout is POST-only and clears the authenticated session
- login POST remains CSRF protected

## Fresh database smoke test

A fresh SQLite database was created with the bundled migrations and seeded using:

```text
python manage.py migrate
python manage.py seed_demo --reset --demo-user
```

Demo login:

```text
student / PlanitDemo123!
```

Authenticated smoke checks returned HTTP `200` for:

```text
/
/tasks/
/courses/
/projects/
/api/tasks/
/api/today/
/api/week/
/api/subjects/
/api/projects/
/api/task-options/
```

Signed out checks returned:

```text
/login/       200
/             302 -> login
/api/tasks/   401 JSON
```

The Today payload also returned a populated `top_focus` object derived from the Python attention-ranking service.

## Static-source verification

- all Planit JavaScript files passed `node --check`
- bundled Bootstrap JavaScript passed `node --check`
- `style.css` parsed with `tinycss2` with zero stylesheet parse errors
- bundled Bootstrap CSS parsed with zero stylesheet parse errors
- Bootstrap remains bundled locally; no Bootstrap CDN is required
- theme preference and Exam Mode use separate `localStorage` keys
- semantic primary/mobile navigation uses `<nav>`, `<ul>`, `<li>`, and `<a>`
- login animation includes `transform: scale()` motion and respects `prefers-reduced-motion`

## Data-package verification

The final ZIP intentionally excludes:

```text
.venv/
db.sqlite3
__pycache__/
*.pyc
.DS_Store
__MACOSX/
```

This prevents machine-specific environments, local accounts, and personal database data from being submitted accidentally.
