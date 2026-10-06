# Planit Presentation Guide

## Suggested 6–8 minute demo order

### 1. Problem and goal — 30 seconds

Planit combines academic and personal planning in one responsive student-focused interface. The project intentionally connects the two courses: dynamic web technology on the frontend and Functions/OOP on the Python backend.

### 2. Today — 60 seconds

Show real database data, progress, overdue tasks, and next exam. Toggle Academic/Personal. Turn Exam Mode on and refresh to demonstrate `localStorage` persistence.

Explain:

```text
Browser -> GET /api/today/ -> Django -> OOP/services -> JSON -> DOM
```

### 3. Task CRUD — 90 seconds

Create a task from Add task, edit it, mark it complete, then delete it. Keep Network > Fetch/XHR visible for one action.

Point out:

```text
POST   create
PATCH  edit / complete
DELETE delete
X-CSRFToken protects unsafe requests
```

### 4. Tasks / This Week — 45 seconds

Show search, area filter, priority/status/subject filters, and sorting. Turn on Exam Mode and show a past exam still visible but dimmed in This Week.

### 5. Courses + Grade Calculator — 90 seconds

Open the seeded course and demonstrate the canonical case:

```text
Assignment: 20%, score 18/20 -> 18 course points
Midterm:    30%, score 24/30 -> 24 course points
Earned = 42 points
Remaining weight = 50%
Target = 80%
Required remaining average = (80 - 42) / 50 × 100 = 76%
```

Emphasize that the calculation comes from Python `GradeBook`, not duplicated JavaScript math.

### 6. Projects — 45 seconds

Show a project, linked tasks, and automatic progress. Complete a linked task and show progress change.

### 7. Python Functions & OOP — 60 seconds

Show these exact examples:

```text
PlannerItem = abstract base class
GeneralItem / StudyItem / ExamItem / PersonalItem = inheritance
visible_in_exam_mode() = polymorphism
GradeComponent.score = encapsulation
GradeBook contains GradeComponent = composition
select(items, predicate) = higher-order function
by_area() / by_status() = functions returning functions
compose() = predicate composition
```

### 8. Quality — 30 seconds

Mention responsive design, CSRF, layered validation, automated tests, local Bootstrap, safe DOM `textContent`, and clean packaging.

## Likely questions

**Why Django?**  
It integrates the required Python Functions/OOP work with a real dynamic website, database, HTTP endpoints, validation, and server-side business logic.

**Why not calculate grades in JavaScript?**  
Keeping one authoritative Python rule prevents inconsistent calculations across pages and directly demonstrates the Python course requirements.

**What makes this dynamic?**  
Pages fetch JSON from Django, render database records with DOM APIs, and mutate data through POST/PATCH/DELETE without hardcoding task content into HTML.

**What is a higher-order function in your project?**  
`select(items, predicate)` accepts a function, while `by_area` and `by_status` return predicate functions.

**What is polymorphism here?**  
Different `PlannerItem` subclasses implement the same `visible_in_exam_mode(today)` interface with different behavior.

**Why SQLite?**  
It is appropriate for the scope of a single-user coursework prototype and integrates directly with Django ORM.

**Is it production-ready?**  
It is a robust coursework prototype, not a multi-user public service. Authentication, production HTTPS/security settings, deployment infrastructure, and multi-user ownership are future work.

## Presentation-ready v4 additions

For questions about login, logout, wrong passwords, runserver routing, CSS framework, JSON, Fetch API, semantic navigation, or website modes, use:

- `docs/PRESENTATION_READY_V4.md`
- `docs/TEACHER_QA_CHEATSHEET.md`
- `docs/CODE_LOCATION_MAP.md`
- `docs/RUNSERVER_FLOW.md`

During the demo, sign in with the local demo account created by `python manage.py seed_demo --reset --demo-user`, then demonstrate Mint Day / Night Quest separately from Exam Mode so the distinction between UI state and Python business logic is clear.
