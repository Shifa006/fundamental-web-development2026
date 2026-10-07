# Planit v5 changes

## Accounts and security
- `/signup/`: username + unique (case-insensitive) e-mail + password/confirm; auto sign-in afterwards.
- Password rules (`AUTH_PASSWORD_VALIDATORS`): 8+ chars, not common, not all numeric, not similar to username, plus `planner/password_validators.py` (upper, lower, digit, special). Passwords are hashed by Django.
- Per-user data: `owner` FK on Subject, Project, Task (Assessment via its subject). Every query/lookup in `views.py` is filtered by `request.user`; other users' ids return 404. Migration `0004_owner_per_user` assigns existing rows to the first user.
- `seed_demo` now creates the data for user `student` (use `--demo-user` to set the demo password).

## Bugs fixed
- Courses card footer "1 pending0 overdue" -> "1 pending · 0 overdue".
- Floating "+" button no longer covers page content (more bottom padding).
- Game jargon removed from visible copy (quest/inventory/PLAYER LOGIN -> task/tasks/SIGN IN).

## Accessibility
- Visible focus ring, 44px minimum touch targets, reduced-motion support, field errors with role="alert".

## Not verified
- Written without a Django runtime available: run `python manage.py migrate && python manage.py test` before presenting.

## Still recommended (not done)
Account/Change-password page, undo toast after delete/complete, skeleton loading, onboarding empty state for new accounts, visible Edit/Delete buttons, consistent priority colours + text labels, Google OAuth (django-allauth, env vars only).

---

# v1.3 additions (same package)

## New features
- **Month view** (Tasks > Month): read-only calendar with coloured dots, click a day to see its tasks, previous/next/today, "+ Add a task on this day". API: `GET /api/month/?year=&month=&area=&exam_mode=`.
- **Module framework**: `UserSettings`, `planner/modules.py` (`Module` ABC + registry, empty for now), `GET/PATCH /api/settings/`, `GET /api/modules/`. Today response includes `modules` cards. Future modules (Habits, Reading, Reflection, Goals, Faith) plug in by subclassing `Module` — see `docs/Planit_Master_Specification_v1.3_patch.md`.
- **Less retyping**: the Add-task form remembers the last area/type/priority/subject; standard assessment template when creating a course (Quiz 10 / Midterm 30 / Assignment 20 / Final 40); "Add review tasks" (7/3/1 days before) when creating an exam; **Duplicate** button; Today banner suggesting Exam Mode when an unfinished exam is 0-14 days away (dismiss remembered per day).
- **Priority pill colours** are now consistent (urgent = coral, normal = blue, later = grey) and always carry text.

## Verified
- `python manage.py check`, `makemigrations --check`, and `python manage.py test` (95 tests at v1.3; 104 at v1.4) all pass.
- Checked in Chromium at 1360px and 390px: login, Today banner, Month view, add exam with review tasks, remembered defaults, duplicate, course template, no horizontal scroll.

## Not included (see spec v1.3 for the plan)
Habits, Reading, Reflection/Memory, Goals, Faith (prayer times, Hijri, Ramadan), recurring tasks, Account/Change-password page, Google sign-in, undo toast.

## v1.4 additions
- Sign-up password field: HTML5 `pattern`, `minlength`, `maxlength`, `title`; `novalidate` removed from the sign-up form. Server validators remain the authority.
- Tasks page: `countByStatus()` uses `Array.prototype.reduce` to show task counts in the Status filter (e.g. `Overdue (1)`).
- 6 new tests (`tests/test_v14.py`); suite is now 104 tests.
- Password rule: the special character must not be whitespace (server `ComplexityValidator` and HTML `pattern` agree); new `MaxLengthValidator` (128) on the server.
- Status counts in the Status filter also refresh on Week/Month views.
- Grade calculator: when every assessment is graded and the target is missed, the result card shows the final course total and the shortfall instead of "No remaining assessments."
