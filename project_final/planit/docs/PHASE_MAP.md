# Planit — Phase Map

| Phase | Deliverable | Main implementation |
|---|---|---|
| 1 | Foundation + UI | Django project/app, models, routes, templates, responsive visual system |
| 2 | Functions + OOP | `domain.py`, `services.py`, unit tests |
| 3 | API + Fetch + DOM | read APIs, serializers, `api.js`, Today/Tasks dynamic rendering |
| 4 | Task CRUD | POST/PATCH/DELETE, CSRF, task modal, validation, database persistence |
| 5 | Courses + Grade Calculator | Subject/Assessment APIs and UI, `GradeBook`, target calculations |
| 6 | Projects | Project APIs/UI, linked tasks, derived progress |
| 7 | Quality | model/database constraints, error/loading/empty states, responsive fixes, demo seed, expanded tests |
| 8 | Final delivery | README, architecture, article draft, screenshots checklist, presentation guide, final checklist |

## Course concepts demonstrated

### Fundamental Web Development

- semantic HTML
- responsive CSS and Bootstrap
- JavaScript events and DOM manipulation
- higher-order array methods (`filter`, `sort`, `forEach`)
- Fetch API
- Promises through `async` / `await`
- JSON
- HTTP methods and status codes
- Web Storage (`localStorage`)
- CSRF-aware browser requests

### Python — Functions & OOP

- reusable functions and top-down decomposition
- functions passed as arguments (`select(items, predicate)`)
- functions returning predicates (`by_area`, `by_status`)
- predicate composition (`compose`)
- abstract base class (`PlannerItem`)
- inheritance (`GeneralItem`, `StudyItem`, `ExamItem`, `PersonalItem`)
- polymorphism (`visible_in_exam_mode`)
- encapsulation (`GradeComponent.score` property)
- composition (`GradeBook` contains `GradeComponent` objects)
