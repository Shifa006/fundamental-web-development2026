# Code Location Map

| Topic | Main file(s) |
| --- | --- |
| Django settings | `config/settings.py` |
| Project URL entry | `config/urls.py` |
| Planit routes | `planner/urls.py` |
| Login / logout | `planner/views.py`, `planner/templates/planner/login.html` |
| Auth protection | `planner/middleware.py` |
| Models / SQLite schema | `planner/models.py` |
| OOP | `planner/domain.py` |
| Functions / HOF | `planner/services.py` |
| Validation | `planner/validators.py` |
| JSON APIs | `planner/views.py` |
| Fetch wrapper | `planner/static/planner/js/api.js` |
| Theme/localStorage | `planner/static/planner/js/theme.js` |
| Exam Mode/localStorage | `planner/static/planner/js/ui.js` |
| DOM Today | `planner/static/planner/js/today.js` |
| DOM Tasks / filters | `planner/static/planner/js/tasks.js` |
| CRUD forms | `planner/static/planner/js/task-actions.js`, `courses.js`, `projects.js` |
| HTML shell + semantic nav | `planner/templates/planner/base.html` |
| Bootstrap modals | `planner/templates/planner/includes/modals.html` |
| Custom CSS | `planner/static/planner/css/style.css` |
| Local Bootstrap | `planner/static/vendor/bootstrap/` |
| Demo data | `planner/management/commands/seed_demo.py` |
| Tests | `planner/tests/` |
