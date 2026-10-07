# Manual Browser Test Plan

Run `python manage.py seed_demo --reset` before this checklist when you want a predictable demonstration dataset.

## Today

1. Open `/` and confirm Today data loads from `/api/today/`.
2. Toggle All / Academic / Personal and verify content changes.
3. Turn Exam Mode on; verify a new request uses `exam_mode=1`.
4. Refresh; Exam Mode should remain on through `localStorage`.
5. Complete a due-today task; Today progress should refresh from the database.

## Tasks

1. Open `/tasks/` and verify All Tasks renders database records.
2. Search by task title, description, subject/course code, and project title.
3. Test Area, Priority, Status, Subject filters.
4. Test Attention, Due date, Priority sorting.
5. Switch to This Week and repeat search/filter/sort without page reload.
6. With Exam Mode on, verify past exams remain visible but dimmed in This Week.
7. Confirm ACTIVE count changes with current filters/view.

## CRUD

1. Add a task and confirm POST 201.
2. Edit it and confirm PATCH 200.
3. Complete/uncomplete and confirm PATCH 200.
4. Delete it and confirm DELETE 204.
5. Refresh after each mutation to verify persistence.

## Validation

1. Personal + Exam should be rejected.
2. Exam without due date should be rejected.
3. Project/subject mismatch should be rejected.
4. Assessment score above max should be rejected.
5. Assessment total configured weight above 100 should be rejected.

## Courses / Grade Calculator

1. Create/edit/delete a course.
2. Create/edit/delete assessments.
3. Use the seeded canonical course and target 80%; required remaining average should be 76%.

## Projects

1. Create/edit/delete project.
2. Add linked task.
3. Mark linked task complete and verify progress changes.
4. Try changing a project subject when linked tasks conflict; request should be rejected.

## Responsive / accessibility

At 390px width:

- bottom navigation visible
- no horizontal page overflow
- modal Cancel buttons visible
- Add/Edit forms usable
- keyboard focus visible
- reduced-motion system preference does not break layout

## DevTools

- Console: no red uncaught errors
- Network > Fetch/XHR: expected HTTP methods/status codes
- POST/PATCH/DELETE request includes `X-CSRFToken`
- user-entered HTML-like text displays as text rather than executing
