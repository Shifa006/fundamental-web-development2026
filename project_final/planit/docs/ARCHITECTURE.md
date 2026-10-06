# Planit Architecture

## Request flow

```text
User action
   ↓
HTML / DOM event
   ↓
JavaScript
   ↓
PlanitAPI (Fetch + JSON + CSRF)
   ↓
Django URL route
   ↓
API view
   ↓
Normalization / validation
   ↓
Services + OOP domain rules
   ↓
Django ORM
   ↓
SQLite
   ↓
JSON response
   ↓
DOM re-render
```

## Layer responsibilities

### `models.py`
Persistent entities and core data invariants. Model validation protects Django Admin, while database check constraints protect critical rules even when application-level validation is bypassed.

### `domain.py`
Python-only business objects. It does not depend on Django ORM. `PlannerItem` and subclasses calculate status, attention score, and Exam Mode visibility. `GradeComponent` and `GradeBook` calculate grade outcomes.

### `services.py`
Reusable application functions. It converts ORM tasks into domain objects, performs higher-order filtering, sorting, Today payload construction, project progress, and JSON-friendly serialization.

### `validators.py`
Normalizes incoming JSON and rejects invalid API input before persistence.

### `views.py`
Coordinates HTTP requests and responses. It chooses the correct validator/service/model operations and returns consistent JSON errors.

### Browser JavaScript
Handles interaction and presentation only. Important business rules such as task status, Exam Mode eligibility, grade calculations, and project progress come from Python rather than being reimplemented independently in the browser.

## Main model relationships

```text
Subject 1 ─── * Task
Subject 1 ─── * Project
Subject 1 ─── * Assessment
Project 1 ─── * Task
```

Deletion policy:

```text
Delete Subject
  → Assessments deleted (CASCADE)
  → Tasks keep existing but subject becomes NULL
  → Projects keep existing but subject becomes NULL

Delete Project
  → Tasks keep existing but project becomes NULL
```

## Task business matrix

```text
Academic + General      valid
Academic + Assignment   valid
Academic + Study        valid
Academic + Exam         valid (due date required)
Personal + General      valid
Personal + other kinds  invalid
Personal + Subject      invalid
Personal + Project      invalid
```

When an academic task is attached to a project that has a subject, the task inherits that subject unless an incompatible subject was supplied, in which case the request is rejected.

## HTTP API summary

```text
GET     /api/tasks/
POST    /api/tasks/
PATCH   /api/tasks/<id>/
DELETE  /api/tasks/<id>/
GET     /api/today/
GET     /api/week/

GET/POST          /api/subjects/
GET/PATCH/DELETE  /api/subjects/<id>/
GET               /api/subjects/<id>/grade/

POST              /api/assessments/
PATCH/DELETE      /api/assessments/<id>/

GET/POST          /api/projects/
GET/PATCH/DELETE  /api/projects/<id>/
```

Representative status codes: `200`, `201`, `204`, `400`, `403`, `404`, `405`.

## Authentication layer added in Presentation-Ready v4

```text
Browser request
      ↓
Django SessionMiddleware
      ↓
AuthenticationMiddleware
      ↓
PlanitAuthenticationMiddleware
      ├─ authenticated → continue
      ├─ signed-out page → redirect /login/?next=...
      └─ signed-out /api/* → JSON 401
```

`login_page()` uses Django `authenticate()` and `login()`. `logout_page()` is POST-only and calls Django `logout()`.

Theme mode is intentionally outside this business/authentication path: `theme.js` stores `planit_theme` in localStorage and changes CSS variables only.
