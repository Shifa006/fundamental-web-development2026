# Planit Pastel Quest UI v3

This release keeps the Django/Python business logic from Final Clean v2 and replaces the visual system with a pastel digital-quest interface inspired by compact mobile apps, retro game menus, quest boards, and soft mint/lavender/yellow UI.

## Visual direction

- warm cream background
- mint, sage, aqua, lavender, butter, peach accents
- dark ink outlines
- offset cartoon/game shadows
- capsule filters and segmented controls
- quest-board task cards
- app-style dark sidebar and mobile bottom navigation
- floating add-task button
- responsive desktop/tablet/mobile layouts
- no emoji dependency and no remote font dependency

## Files intentionally changed

### Templates
- `planner/templates/planner/base.html`
- `planner/templates/planner/today.html`
- `planner/templates/planner/tasks.html`
- `planner/templates/planner/courses.html`
- `planner/templates/planner/projects.html`
- `planner/templates/planner/includes/modals.html`

### Static UI
- `planner/static/planner/css/style.css`
- `planner/static/planner/js/ui.js`
- `planner/static/planner/js/today.js`
- `planner/static/planner/js/tasks.js`

### Regression tests
- `planner/tests/test_frontend_contract.py`

## Files kept from Final Clean v2

The API, OOP domain layer, validators, services, models, migrations, task CRUD implementation, Courses logic, Projects logic, local Bootstrap files, and all other backend tests remain compatible with Final Clean v2.

## Important DOM contracts preserved

The redesign keeps the IDs and data attributes used by the JavaScript application, including `examModeButton`, `addTaskButton`, `todayTaskList`, `overdueTaskList`, `weekGrid`, `taskSearch`, the task filters, modal IDs, and CRUD hooks.

## Verification

- `python manage.py check`: passed
- Django tests: 52/52 passed
- all JavaScript files: `node --check` passed
- CSS parsed with zero syntax errors
- Bootstrap remains bundled locally
- Google Fonts removed so the shell has no remote font dependency
