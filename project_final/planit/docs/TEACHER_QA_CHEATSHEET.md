# Teacher Q&A Cheat Sheet

## What framework did you use?

**Django 6.1.2** for the backend. **Bootstrap 5.3.6** is the CSS/UI framework used mainly for modal behavior, while the look is custom CSS. The frontend interaction is vanilla JavaScript.

## How does `python manage.py runserver` know the homepage?

`manage.py` loads `config.settings`. Django then uses `ROOT_URLCONF = "config.urls"`. `config/urls.py` includes `planner.urls`. In `planner/urls.py`, `path("", views.today_page)` maps `/` to `today_page()`, and that view renders `planner/today.html`.

## Where is login?

- Route: `planner/urls.py`
- Logic: `planner/views.py -> login_page`
- Form: `planner/templates/planner/login.html`
- Django functions: `authenticate()` and `login()`

## What happens when the password is wrong?

`authenticate()` returns `None`. Planit keeps the form visible and displays `Incorrect username or password.` It does not compare raw passwords itself.

## Where is logout?

`POST /logout/` calls `django.contrib.auth.logout()` and redirects to `/login/`.

## How are pages protected?

`planner/middleware.py` checks `request.user.is_authenticated`. Browser pages redirect to login. `/api/` endpoints return JSON `401` when the session is missing.

## Where do you use Bootstrap?

Bootstrap is bundled locally under `planner/static/vendor/bootstrap/`. The modal markup uses Bootstrap classes such as `modal`, `fade`, and `modal-dialog`, and JavaScript opens it with `bootstrap.Modal`.

## Where do you use Fetch API?

`planner/static/planner/js/api.js` wraps `fetch()`. Today, Tasks, Courses, and Projects call the reusable API functions.

## What is async/await?

`fetch()` returns a Promise. `await` waits for that Promise inside an async function without freezing the whole browser interface.

## Where do you use DOM?

`today.js`, `tasks.js`, `courses.js`, and `projects.js` create elements with `document.createElement`, set values with `textContent`, and append elements into HTML containers.

## Where do you use High Order Array Methods?

`tasks.js` uses `.filter()` and `.sort()` with callback functions. Python also demonstrates higher-order functions through `select(items, predicate)`, `by_area()`, `by_status()`, and `compose()` in `services.py`.

## Do you use JSON?

Yes. Django APIs return `JsonResponse`. The browser calls `response.json()` after Fetch. Planit uses dynamic JSON generated from SQLite rather than a static `data.json` file.

## What HTTP methods do you use?

- GET: read data
- POST: create
- PATCH: partial update / complete
- DELETE: remove
- 200: success
- 201: created
- 204: deleted with no response body
- 400: invalid input
- 401: not authenticated
- 403: CSRF rejection
- 404: missing resource
- 405: wrong HTTP method

## What are your website modes?

Exam Mode is business logic. Mint Day / Night Quest is a visual theme saved in `localStorage`.

## How does filtering work?

The browser keeps filter state and applies reusable predicates to the task array. Search, area, priority, status, subject, and sorting can be combined.

## Why use `<ul>` and `<li>` in navigation?

Navigation is a collection of related links. `<ul>` and `<li>` give the document clearer semantic structure while `<nav>` identifies it as navigation.

## Where is OOP?

`domain.py` contains the abstract `PlannerItem` base class and subclasses such as `ExamItem`, `StudyItem`, and `PersonalItem`. They override behavior such as `visible_in_exam_mode()`, demonstrating inheritance and polymorphism. `GradeBook` composes `GradeComponent` objects.

## Where are imports/libraries?

Examples in `views.py`:

```python
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .models import Task
```

`from` names the module/package; `import` brings the object into the current file. A leading `.` means import from the current Django app package.
