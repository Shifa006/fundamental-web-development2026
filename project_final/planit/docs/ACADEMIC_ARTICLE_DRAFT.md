# Planit: A Responsive Student Planner Integrating Dynamic Web Development with Python Functions and Object-Oriented Programming

> Draft for final submission. Replace the bracketed evidence placeholders with your own screenshots, testing observations, student/course details, and required citation format before submission.

## Abstract

Planit is a responsive single-user student planner developed to integrate concepts from Fundamental Web Development and Python programming in one application. The system supports task management, academic and personal separation, an Exam Mode, course and assessment management, a grade target calculator, and project tracking with automatically derived progress. The frontend is implemented with semantic HTML, responsive CSS, Bootstrap, and vanilla JavaScript. JavaScript communicates with a Django backend through JSON APIs using the Fetch API and asynchronous `async/await` syntax. The backend uses Django ORM and SQLite for persistence, while reusable Python functions and an object-oriented domain layer implement important business rules. The design deliberately avoids duplicating status, Exam Mode, grade, and project-progress logic in JavaScript so that the Python layer remains authoritative. Testing includes unit, service, API, validation, database-constraint, CSRF, and frontend contract checks. The project demonstrates how web programming concepts and Python Functions/OOP can be combined in a practical student-focused system.

## 1. Introduction

Students commonly manage assignments, exams, personal tasks, course grades, and project deadlines across separate tools. This fragmentation can make prioritization difficult, particularly when several deadlines occur at the same time. Planit was designed as a focused student planner that brings these related responsibilities into one interface while remaining small enough to explain clearly as a coursework project.

The project had an additional academic objective: it needed to demonstrate learning from two subjects in one coherent implementation. The web-development side required a dynamic interface rather than static HTML pages, while the Python side required meaningful use of functions and object-oriented programming. Planit therefore uses the browser as an interactive client and Django as a Python application server. Browser actions become HTTP requests; Django retrieves or updates database records; Python services and domain objects calculate derived information; JSON is returned; and JavaScript updates the DOM.

The resulting system consists of four primary pages: Today, Tasks, Courses, and Projects. This intentionally limited navigation keeps the scope understandable while still supporting full CRUD workflows and several derived features.

## 2. Objectives

The main objectives were to:

1. create a responsive dynamic website suitable for desktop and mobile use;
2. implement task CRUD operations using HTTP GET, POST, PATCH, and DELETE;
3. use Fetch API, JSON, async/await, DOM manipulation, and Web Storage in the browser;
4. apply reusable Python functions and higher-order-function concepts;
5. apply abstraction, inheritance, polymorphism, encapsulation, and composition in a real feature;
6. maintain data using Django ORM and SQLite;
7. validate data consistently and provide useful error responses;
8. implement course/assessment management and a grade target calculator;
9. implement project tracking with progress derived from linked tasks; and
10. test core behavior before final submission.

## 3. System Design

Planit follows a layered design. Django models represent Subject, Project, Task, and Assessment records. API validators normalize incoming JSON and reject invalid user input. The service layer contains reusable functions for filtering, sorting, serialization, summaries, and conversions between ORM records and domain objects. The domain layer contains Python objects that model planner behavior independently from the database.

A typical request follows this path:

```text
Browser event
→ Fetch request
→ Django URL
→ API view
→ validation
→ service/domain logic
→ Django ORM
→ SQLite
→ JSON response
→ DOM update
```

This separation improves explainability. For example, JavaScript does not independently decide whether an exam is overdue or whether a task should appear in Exam Mode. Those decisions come from Python and are serialized to JSON.

[Insert Figure 1: Planit architecture diagram]

## 4. Python Functions and Higher-Order Functions

Planit uses small reusable functions to avoid repeating logic. In the service layer, `select(items, predicate)` receives a function as an argument and applies it as a filter. Functions such as `by_area(area)` and `by_status(today, *statuses)` return predicate functions. `compose(*predicates)` combines multiple predicates into one. These are practical examples of higher-order-function behavior because functions are passed to and returned from other functions.

Top-down decomposition is also visible in payload-building functions. `build_today_payload()` coordinates smaller functions for area filtering, status filtering, completion rate, nearest exam, Exam Mode visibility, and attention sorting rather than implementing every rule inside a single large block.

## 5. Object-Oriented Programming

The task domain uses an abstract base class named `PlannerItem`. It defines shared state and methods such as `status()`, `days_left()`, and `attention_score()`, while requiring subclasses to provide type-specific behavior.

`GeneralItem`, `StudyItem`, `ExamItem`, and `PersonalItem` inherit from `PlannerItem`; `AssignmentItem` inherits the general-item behavior. The method `visible_in_exam_mode(today)` is polymorphic: the browser can ask whether any planner item is visible without knowing the specific subclass, while each subclass applies its own rule.

The grade system demonstrates additional OOP concepts. `GradeComponent` encapsulates score validation through a property setter and private `_score` attribute. `GradeBook` uses composition because it manages a collection of `GradeComponent` objects. The grade calculator shown in the Courses page therefore depends directly on the Python OOP implementation.

## 6. Dynamic Web Implementation

The frontend uses Fetch API and `async/await` to request JSON from Django. For example, the Today page calls `/api/today/`, while Tasks uses `/api/tasks/` and `/api/week/`. The browser then creates DOM elements using methods such as `document.createElement()` and assigns user-controlled text through `textContent`. This avoids relying on hardcoded task HTML and reduces the risk associated with inserting untrusted strings as HTML.

Unsafe requests include an `X-CSRFToken` header. Task creation uses POST, edits and completion changes use PATCH, and deletions use DELETE. Successful creation returns HTTP 201, successful deletion returns 204 with no body, invalid input normally returns 400, missing resources return 404, unsupported methods return 405, and Django CSRF protection can return 403.

Exam Mode uses `localStorage` only for the user's on/off preference. The actual visibility rules remain in Python. This distinction is important: Web Storage remembers presentation preference, while server-side code remains the authoritative source of business behavior.

## 7. Data Validation and Integrity

Validation occurs in layers. Browser controls improve user experience, but the server does not trust browser input. API validators normalize strings, dates, IDs, decimal values, task combinations, and assessment values. Django model validation repeats critical invariants so that Django Admin cannot silently create incompatible data. Database check constraints add another layer for rules that SQLite can enforce directly.

Examples include requiring exams to have due dates, restricting personal tasks to the general type with no academic relations, requiring assessment weight to be within an allowed range, and preventing a recorded score from exceeding its maximum score. The assessment service also prevents the total configured weight of a course from exceeding 100%.

## 8. Grade Target Calculator

The grade calculator converts each graded assessment into weighted course points. The demonstration dataset uses the following case:

```text
Assignment: weight 20, score 18/20 → 18 course points
Midterm:    weight 30, score 24/30 → 24 course points
Project:    weight 20, ungraded
Final:      weight 30, ungraded
```

The student has earned 42 course points from 50% graded weight, producing an 84% average on graded work. If the course target is 80%, 50% course weight remains. The required average on remaining work is:

```text
(80 - 42) / 50 × 100 = 76%
```

The user interface displays the result generated by the Python `GradeBook` rather than recalculating it separately in JavaScript.

[Insert Figure 2: Grade calculator screenshot showing target 80 and required 76]

## 9. Responsive Interface and Usability

Planit uses a desktop sidebar and a mobile bottom navigation. Cards, folder-like course elements, paper/tape motifs, pastel colors, rounded surfaces, and restrained animation create a planner/journal visual identity without changing the underlying information architecture. Responsive breakpoints restructure course, project, Today, and week layouts for smaller screens. Reduced-motion preferences are respected through CSS.

Bootstrap is bundled inside the project rather than required from a CDN, reducing the risk that modal workflows fail during an offline classroom demonstration. Google Fonts are optional; system font fallbacks keep the application usable if external font requests are unavailable.

[Insert Figure 3: desktop Today page]

[Insert Figure 4: 390px mobile view]

## 10. Testing

The project includes automated tests for domain rules, grade calculations, higher-order filtering, service behavior, API responses, CRUD workflows, CSRF enforcement, model validation, database constraints, project progress, course and assessment operations, 404/405 behavior, local Bootstrap availability, and basic rendered-markup contracts.

Before submission, run:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test planner.tests -v 2
```

[Replace this paragraph with the final test count and terminal screenshot from your own machine.]

Manual testing should additionally cover responsive behavior, modal controls, browser Console errors, Network requests, Exam Mode persistence, and the complete create/edit/complete/delete flow.

## 11. Limitations and Future Work

Planit V1 is intentionally an authenticated local prototype. Django session authentication protects the interface and APIs, but all planner records still belong to one shared local workspace rather than separate per-user data stores. The project does not provide public registration, password-reset email, production deployment configuration, notifications, calendar synchronization, or a progressive web application. A future version could add user-specific ownership, recurring tasks, notifications, calendar integrations, PWA support, and production deployment settings.

## 12. Conclusion

Planit demonstrates that the two course areas can support one another rather than appearing as disconnected requirements. Web technologies provide the interactive client, HTTP communication, responsive presentation, and DOM behavior, while Python functions and OOP provide reusable and testable business logic. The Django layer connects these concepts to persistence and validation. The final result is a working student-planning prototype in which course concepts are visible both in the source code and in observable application behavior.

## Evidence to add before submitting

- real screenshots from your final browser build
- final automated-test terminal screenshot and test count
- any required user-testing evidence
- student name/ID/course information
- references formatted using the citation style required by the instructor

## Presentation-ready authentication extension

The final demonstration build adds Django session authentication to the local prototype. Public access is limited to the login page and Django Admin's own authentication routes. When an unauthenticated browser requests a Planit page, middleware redirects the request to the login page with a safe `next` parameter. Unauthenticated API requests return a JSON response with HTTP status 401 so Fetch-based code receives an API-appropriate response rather than an HTML login page.

The interface also includes a user-controlled Mint Day / Night Quest visual theme. This preference is stored in browser localStorage and restored by JavaScript, while Exam Mode remains a separate planner business feature whose visibility rules are calculated by Python domain objects. Keeping these two modes separate helps distinguish presentation state from application business logic.

A Top Focus card was added as a planner-specific analogue to recommendation/ranking features commonly found in dynamic websites. Instead of ranking products, Planit ranks active tasks through the existing attention model, combining status, priority, task type, and due-date proximity in the Python service layer before returning the selected task through JSON.
