# Planit Final Clean v2 — Change Log

This release was rebuilt from the supplied `planit.zip` and rechecked as one integrated codebase.

## Correctness fixes

1. Added model-level validation for Task, Assessment, Subject, and Project data.
2. Added database check constraints for critical Task and Assessment invariants.
3. Fixed Exam Mode hidden-count semantics so it counts every active filtered item hidden by Exam Mode.
4. Fixed This Week so past exams remain visible (dimmed) while Exam Mode is on.
5. Fixed This Week sorting for Attention, Due date, and Priority.
6. Fixed This Week active-count refresh under search/filter changes.
7. Fixed mobile CSS that previously hid every inactive `.soft-button`, including modal Cancel/Edit controls.
8. Removed the unused duplicate `task_modal.html` template.
9. Bundled Bootstrap locally to remove the presentation-time CDN dependency.
10. Corrected duplicated `color` serialization entry in `serialize_task`.
11. Improved Tasks search to include description, subject, course code, and project title.
12. Made project progress count all linked tasks so an unfinished past exam cannot make a project appear complete.
13. Reduced unnecessary repeated week API calls when only client-side search/sort/status/subject filters change.
14. Improved subject-list use of prefetched related data.

## Test expansion

The suite now covers model/database constraints, course CRUD, assessment CRUD/limits, project CRUD/conflicts, missing-resource 404s, method 405s, local Bootstrap/static contracts, markup ID/button checks, and the Exam Mode hidden-count regression.
