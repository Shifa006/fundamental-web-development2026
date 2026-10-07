# Planit Final Checklist

## Code

- [ ] `python manage.py check` returns no issues
- [ ] `python manage.py makemigrations --check --dry-run` says no changes
- [ ] `python manage.py test planner.tests -v 2` passes
- [ ] `python manage.py seed_demo --reset` succeeds
- [ ] Today, Tasks, Courses, Projects all load
- [ ] Browser Console contains no red JavaScript errors

## Task workflow

- [ ] Add task
- [ ] Edit task
- [ ] Complete/uncomplete task
- [ ] Delete task
- [ ] Search/filter/sort works
- [ ] This Week sorts correctly
- [ ] Past exam remains dimmed in This Week under Exam Mode
- [ ] Exam Mode persists after refresh

## Courses and grades

- [ ] Add/edit/delete course
- [ ] Add/edit/delete assessment
- [ ] Total weight above 100 is rejected
- [ ] Score above max score is rejected
- [ ] Canonical target 80% case displays required 76%

## Projects

- [ ] Add/edit/delete project
- [ ] Add linked task
- [ ] Project subject normalization works
- [ ] Project progress updates from task completion

## Responsive / UX

- [ ] Test at 390px wide
- [ ] Modal Cancel buttons remain visible
- [ ] Bottom navigation works
- [ ] No horizontal page overflow
- [ ] Loading, empty, error, and toast states are readable

## Submission package

- [ ] No `.venv/`
- [ ] No `db.sqlite3`
- [ ] No `__pycache__/`
- [ ] No `.DS_Store`
- [ ] No `__MACOSX/`
- [ ] README included
- [ ] Article updated with real screenshots/results
- [ ] Presentation prepared
- [ ] Git working tree clean

## Presentation-ready v4 checks

- [ ] `/login/` renders before authentication
- [ ] wrong password shows a visible error
- [ ] correct login opens Today
- [ ] Logout returns to Login
- [ ] signed-out Planit page redirects to Login
- [ ] signed-out API request returns JSON 401
- [ ] Mint Day / Night Quest survives refresh
- [ ] Exam Mode remains separate from visual theme
- [ ] Top Focus appears from `/api/today/`
- [ ] semantic navigation uses `nav > ul > li > a`
- [ ] `python manage.py test planner.tests -v 2` reports 104 passing tests (on your Django version)
