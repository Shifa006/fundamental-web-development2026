# Planit Presentation-Ready v4

This release adds the features most likely to be useful during a live code explanation without changing Planit's core academic scope.

## What was added

- Django login form and POST-only logout
- Session authentication for Planit pages
- JSON `401` response for unauthenticated API requests
- Wrong-password feedback without manual password comparison
- Login zoom/fade motion with reduced-motion support
- Mint Day / Night Quest theme stored in `localStorage`
- Semantic navigation using `<nav>`, `<ul>`, `<li>`, and `<a>`
- Top Focus card derived from the Python attention-ranking service
- Demo-user option in `seed_demo`
- Authentication and frontend contract tests

## Framework answers

### Website framework

**Django 6.1.2** is the backend web framework. It provides URL routing, views, templates, authentication, sessions, CSRF protection, ORM access, and response objects.

### CSS framework

**Bootstrap 5.3.6** is bundled locally. Planit mainly uses Bootstrap for modal behavior and accessibility. The visual system is custom CSS in `planner/static/planner/css/style.css`.

### JavaScript framework

Planit does **not** use React or Vue. It uses vanilla JavaScript because the project can demonstrate DOM manipulation, Fetch API, Promises/async-await, array higher-order methods, JSON, events, and Web Storage directly.

## How `runserver` finds the homepage

```text
python manage.py runserver
        ↓
manage.py loads config.settings
        ↓
Django starts development server
        ↓
Browser requests GET /
        ↓
config/urls.py
        ↓
include("planner.urls")
        ↓
planner/urls.py
        ↓
path("", views.today_page, name="today")
        ↓
planner/views.py -> today_page()
        ↓
render("planner/today.html")
        ↓
HTML response
        ↓
Browser loads CSS + JavaScript
        ↓
JavaScript fetches /api/today/
        ↓
JSON -> DOM
```

Django does not automatically open `today.html`. The URL route decides which view runs, and the view decides which template to render.

## Login flow

```text
GET /login/
   ↓
login.html
   ↓
POST username + password + CSRF token
   ↓
authenticate(request, username, password)
   ↓
correct? ── yes ──> login(request, user) -> session -> redirect /
   │
   no
   ↓
"Incorrect username or password."
```

Passwords are not compared manually in Planit. Django authentication verifies the submitted password against the stored password hash.

## Logout flow

```text
POST /logout/
   ↓
logout(request)
   ↓
session authentication cleared
   ↓
redirect /login/
```

Logout is POST-only so navigation links do not accidentally log the user out.

## Fetch API flow

```text
Browser event
   ↓
PlanitAPI.get/post/patch/delete
   ↓
fetch()
   ↓
Promise
   ↓
await response
   ↓
response.json()
   ↓
JavaScript object
   ↓
DOM rendering
```

For unsafe requests, `api.js` also sends `X-CSRFToken`.

## Static JSON vs Planit JSON

Planit does not use a static `data.json` file as its main data source.

```text
SQLite
  ↓
Django ORM
  ↓
Python services/domain rules
  ↓
JsonResponse
  ↓
Fetch API
  ↓
DOM
```

This makes the JSON dynamic and database-backed.

## Filters and higher-order array methods

The Tasks page uses functions such as:

```javascript
tasks
    .filter((task) => matchesClientFilters(task))
    .sort(taskSortComparator);
```

`.filter()` and `.sort()` receive functions as arguments, so they are higher-order array methods.

## DOM example

Planit does not hard-code every database task into HTML. JavaScript creates elements after receiving JSON:

```javascript
const article = document.createElement("article");
const title = document.createElement("strong");
title.textContent = task.title;
article.append(title);
```

`textContent` is used for user-controlled text instead of `innerHTML`.

## Website modes

Planit has two different modes:

1. **Exam Mode** — a business feature. Python decides which tasks deserve focus.
2. **Mint Day / Night Quest** — a visual theme. JavaScript stores the preference in `localStorage` and CSS variables change the appearance.

## Top Focus vs "most seller product"

A store might calculate a best-selling product. Planit instead calculates the most important active task.

The Top Focus card comes from the Python service layer:

```text
active tasks
   ↓
status / priority / type / due-date rules
   ↓
attention score + sort_by_attention()
   ↓
highest-ranked task
   ↓
/api/today/ JSON
   ↓
Top Focus card
```

This is more appropriate to a planner than adding an unrelated shopping feature.
