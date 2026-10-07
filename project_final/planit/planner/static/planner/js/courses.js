document.addEventListener("DOMContentLoaded", () => {
    initCoursesPage();
});

let subjects = [];
let selectedSubject = null;
let editingSubjectId = null;
let editingAssessmentId = null;


async function initCoursesPage() {
    document.querySelector("#addSubjectButton")?.addEventListener("click", openCreateSubject);
    document.querySelector("#subjectForm")?.addEventListener("submit", submitSubjectForm);
    document.querySelector("#assessmentForm")?.addEventListener("submit", submitAssessmentForm);
    document.querySelector("#editSubjectButton")?.addEventListener("click", () => {
        if (selectedSubject) {
            openEditSubject(selectedSubject);
        }
    });
    document.querySelector("#deleteSubjectButton")?.addEventListener("click", deleteSelectedSubject);
    document.querySelector("#addAssessmentButton")?.addEventListener("click", openCreateAssessment);
    document.querySelector("#calculateGradeButton")?.addEventListener("click", calculateGrade);

    document.addEventListener("planit:tasks-changed", async () => {
        await loadSubjects();
        if (selectedSubject) {
            await loadSubjectDetail(selectedSubject.id);
        }
    });

    await loadSubjects();
}


async function loadSubjects() {
    showCoursesLoading();

    try {
        const data = await window.PlanitAPI.get("/api/subjects/");
        subjects = data.subjects;
        renderSubjects();
        document.querySelector("#coursesLoading").hidden = true;
        document.querySelector("#courseGrid").hidden = false;
    } catch (error) {
        showCoursesError(error.message);
    }
}


function renderSubjects() {
    const grid = document.querySelector("#courseGrid");
    grid.replaceChildren();

    if (!subjects.length) {
        grid.append(window.PlanitUtils.emptyMessage("No courses yet. Add your first course."));
        return;
    }

    subjects.forEach((subject, index) => {
        const article = document.createElement("article");
        article.className = `course-folder ${subject.color}-folder reveal`;

        const tab = document.createElement("div");
        tab.className = "folder-tab";
        tab.textContent = subject.code || `COURSE ${String(index + 1).padStart(2, "0")}`;

        const paper = document.createElement("div");
        paper.className = "folder-paper";

        const number = document.createElement("div");
        number.className = "course-index";
        number.textContent = String(index + 1).padStart(2, "0");

        const name = document.createElement("h2");
        name.textContent = subject.name;

        const meta = document.createElement("p");
        meta.textContent = subject.semester || "Current semester";

        const progress = document.createElement("div");
        progress.className = "course-progress";

        const progressTop = document.createElement("div");
        const label = document.createElement("span");
        label.textContent = "Task completion";
        const value = document.createElement("strong");
        const percent = subject.summary.completion.percent;
        value.textContent = percent === null ? "--" : `${percent}%`;
        progressTop.append(label, value);

        const track = document.createElement("div");
        track.className = "progress-track";
        const bar = document.createElement("span");
        bar.style.width = `${percent ?? 0}%`;
        track.append(bar);
        progress.append(progressTop, track);

        const footer = document.createElement("footer");
        const pending = document.createElement("span");
        pending.textContent = `${subject.summary.pending} pending`;
        const overdue = document.createElement("span");
        overdue.textContent = `${subject.summary.overdue} overdue`;
        footer.append(pending, document.createTextNode(" \u00b7 "), overdue);

        const open = document.createElement("button");
        open.type = "button";
        open.className = "folder-open-button";
        open.textContent = "Open course";
        open.addEventListener("click", () => loadSubjectDetail(subject.id));

        paper.append(number, name, meta, progress, footer, open);
        article.append(tab, paper);
        grid.append(article);
    });
}


async function loadSubjectDetail(subjectId) {
    try {
        const data = await window.PlanitAPI.get(`/api/subjects/${subjectId}/`);
        selectedSubject = data.subject;
        renderSubjectDetail(selectedSubject);
        document.querySelector("#courseDetail").hidden = false;
        document.querySelector("#courseDetail").scrollIntoView({ behavior: "smooth", block: "start" });
        await calculateGrade();
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


function renderSubjectDetail(subject) {
    window.PlanitUtils.setText("#courseDetailCode", subject.code || "COURSE");
    window.PlanitUtils.setText("#courseDetailName", subject.name);
    window.PlanitUtils.setText("#courseDetailSemester", subject.semester || "No semester label");

    const completion = subject.summary.completion;
    window.PlanitUtils.setText(
        "#courseCompletion",
        completion.percent === null ? "--" : `${completion.percent}%`,
    );
    window.PlanitUtils.setText(
        "#courseCompletionMeta",
        completion.total === 0
            ? "No tasks yet"
            : `${completion.completed} of ${completion.total} completed`,
    );
    window.PlanitUtils.setText("#coursePending", subject.summary.pending);
    window.PlanitUtils.setText("#courseOverdue", subject.summary.overdue);

    renderCourseTasks(subject.tasks);
    renderAssessments(subject.assessments);
}


function renderCourseTasks(courseTasks) {
    const list = document.querySelector("#courseTaskList");
    list.replaceChildren();

    if (!courseTasks.length) {
        list.append(window.PlanitUtils.emptyMessage("No tasks linked to this course."));
        return;
    }

    courseTasks.slice(0, 8).forEach((task) => {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "mini-list-row";

        const copy = document.createElement("span");
        const title = document.createElement("strong");
        title.textContent = task.title;
        const meta = document.createElement("small");
        meta.textContent = window.PlanitUtils.taskStatusLabel(task);
        copy.append(title, meta);

        const tag = document.createElement("span");
        tag.className = `task-status ${window.PlanitUtils.kindClass(task.kind)}`;
        tag.textContent = window.PlanitUtils.formatKind(task.kind);

        row.append(copy, tag);
        row.addEventListener("click", () => window.PlanitTasks.openEdit(task));
        list.append(row);
    });
}


function renderAssessments(assessments) {
    const list = document.querySelector("#assessmentList");
    list.replaceChildren();

    if (!assessments.length) {
        list.append(window.PlanitUtils.emptyMessage("No assessments configured yet."));
        return;
    }

    assessments.forEach((assessment) => {
        const row = document.createElement("div");
        row.className = "assessment-row";

        const copy = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = assessment.name;
        const meta = document.createElement("span");
        meta.textContent = assessment.score === null
            ? `${assessment.weight}% · not graded`
            : `${assessment.weight}% · ${assessment.score} / ${assessment.max_score}`;
        copy.append(name, meta);

        const actions = document.createElement("div");
        actions.className = "task-actions";

        const edit = document.createElement("button");
        edit.type = "button";
        edit.className = "text-action";
        edit.textContent = "Edit";
        edit.addEventListener("click", () => openEditAssessment(assessment));

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "text-action danger-action";
        remove.textContent = "Delete";
        remove.addEventListener("click", () => deleteAssessment(assessment));

        actions.append(edit, remove);
        row.append(copy, actions);
        list.append(row);
    });
}


function openCreateSubject() {
    editingSubjectId = null;
    document.querySelector("#subjectForm").reset();
    document.querySelector("#subjectFormError").hidden = true;
    document.querySelector("#subjectTemplateField").hidden = false;
    window.PlanitUtils.setText("#subjectModalTitle", "Add course");
    window.PlanitUtils.setText("#subjectSubmitButton", "Save course");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#subjectModal")).show();
}


function openEditSubject(subject) {
    editingSubjectId = subject.id;
    document.querySelector("#subjectFormError").hidden = true;
    document.querySelector("#subjectTemplateField").hidden = true;
    document.querySelector("#subjectName").value = subject.name;
    document.querySelector("#subjectCode").value = subject.code || "";
    document.querySelector("#subjectSemester").value = subject.semester || "";
    document.querySelector("#subjectColor").value = subject.color;
    window.PlanitUtils.setText("#subjectModalTitle", "Edit course");
    window.PlanitUtils.setText("#subjectSubmitButton", "Save changes");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#subjectModal")).show();
}


async function submitSubjectForm(event) {
    event.preventDefault();
    const errorBox = document.querySelector("#subjectFormError");
    const submit = document.querySelector("#subjectSubmitButton");
    errorBox.hidden = true;
    submit.disabled = true;

    const payload = {
        name: document.querySelector("#subjectName").value,
        code: document.querySelector("#subjectCode").value,
        semester: document.querySelector("#subjectSemester").value,
        color: document.querySelector("#subjectColor").value,
    };

    if (!editingSubjectId && document.querySelector("#subjectTemplate")?.checked) {
        payload.with_default_assessments = true;
    }

    try {
        const response = editingSubjectId
            ? await window.PlanitAPI.patch(`/api/subjects/${editingSubjectId}/`, payload)
            : await window.PlanitAPI.post("/api/subjects/", payload);

        bootstrap.Modal.getInstance(document.querySelector("#subjectModal"))?.hide();
        selectedSubject = response.subject;
        window.PlanitUtils.showToast(editingSubjectId ? "Course updated." : "Course added.");
        document.dispatchEvent(new CustomEvent("planit:options-changed"));
        await loadSubjects();
        await loadSubjectDetail(response.subject.id);
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
    } finally {
        submit.disabled = false;
    }
}


async function deleteSelectedSubject() {
    if (!selectedSubject) {
        return;
    }

    const impact = selectedSubject.delete_impact;
    const message = [
        `Delete "${selectedSubject.name}"?`,
        impact ? `${impact.assessments_deleted} assessments will be deleted.` : "",
        impact ? `${impact.tasks_detached} tasks and ${impact.projects_detached} projects will be detached.` : "",
    ].filter(Boolean).join("\n");

    if (!window.confirm(message)) {
        return;
    }

    try {
        await window.PlanitAPI.delete(`/api/subjects/${selectedSubject.id}/`);
        selectedSubject = null;
        document.querySelector("#courseDetail").hidden = true;
        document.dispatchEvent(new CustomEvent("planit:options-changed"));
        document.dispatchEvent(new CustomEvent("planit:tasks-changed"));
        window.PlanitUtils.showToast("Course deleted.");
        await loadSubjects();
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


function openCreateAssessment() {
    if (!selectedSubject) {
        return;
    }

    editingAssessmentId = null;
    document.querySelector("#assessmentForm").reset();
    document.querySelector("#assessmentFormError").hidden = true;
    window.PlanitUtils.setText("#assessmentModalTitle", "Add assessment");
    window.PlanitUtils.setText("#assessmentSubmitButton", "Save assessment");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#assessmentModal")).show();
}


function openEditAssessment(assessment) {
    editingAssessmentId = assessment.id;
    document.querySelector("#assessmentFormError").hidden = true;
    document.querySelector("#assessmentName").value = assessment.name;
    document.querySelector("#assessmentWeight").value = assessment.weight;
    document.querySelector("#assessmentMaxScore").value = assessment.max_score;
    document.querySelector("#assessmentScore").value = assessment.score ?? "";
    window.PlanitUtils.setText("#assessmentModalTitle", "Edit assessment");
    window.PlanitUtils.setText("#assessmentSubmitButton", "Save changes");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#assessmentModal")).show();
}


async function submitAssessmentForm(event) {
    event.preventDefault();

    if (!selectedSubject) {
        return;
    }

    const errorBox = document.querySelector("#assessmentFormError");
    const submit = document.querySelector("#assessmentSubmitButton");
    errorBox.hidden = true;
    submit.disabled = true;

    const payload = {
        subject_id: selectedSubject.id,
        name: document.querySelector("#assessmentName").value,
        weight: document.querySelector("#assessmentWeight").value,
        max_score: document.querySelector("#assessmentMaxScore").value,
        score: document.querySelector("#assessmentScore").value || null,
    };

    try {
        if (editingAssessmentId) {
            await window.PlanitAPI.patch(`/api/assessments/${editingAssessmentId}/`, payload);
        } else {
            await window.PlanitAPI.post("/api/assessments/", payload);
        }

        bootstrap.Modal.getInstance(document.querySelector("#assessmentModal"))?.hide();
        window.PlanitUtils.showToast(editingAssessmentId ? "Assessment updated." : "Assessment added.");
        await loadSubjectDetail(selectedSubject.id);
        await loadSubjects();
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
    } finally {
        submit.disabled = false;
    }
}


async function deleteAssessment(assessment) {
    if (!window.confirm(`Delete "${assessment.name}"?`)) {
        return;
    }

    try {
        await window.PlanitAPI.delete(`/api/assessments/${assessment.id}/`);
        window.PlanitUtils.showToast("Assessment deleted.");
        await loadSubjectDetail(selectedSubject.id);
        await loadSubjects();
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


async function calculateGrade() {
    if (!selectedSubject) {
        return;
    }

    const target = document.querySelector("#gradeTarget").value || "80";
    const result = document.querySelector("#gradeResult");

    try {
        const data = await window.PlanitAPI.get(
            `/api/subjects/${selectedSubject.id}/grade/?target=${encodeURIComponent(target)}`
        );
        renderGradeResult(data.grade);
    } catch (error) {
        result.textContent = error.message;
        result.classList.add("is-error");
    }
}


function renderGradeResult(grade) {
    const result = document.querySelector("#gradeResult");
    result.classList.remove("is-error");
    result.replaceChildren();

    const headline = document.createElement("strong");
    const detail = document.createElement("span");

    if (grade.status === "incomplete_configuration") {
        headline.textContent = "Complete the grade structure first.";
        detail.textContent = `Configured weight: ${grade.configured_weight}% of 100%.`;
    } else if (grade.status === "achieved") {
        headline.textContent = "Target already achieved.";
        detail.textContent = `Course total so far: ${grade.earned_course_points}% (target ${grade.target}%).`;
    } else if (grade.status === "possible") {
        headline.textContent = `${grade.required}% required on remaining work.`;
        detail.textContent = `Target ${grade.target}% · earned ${grade.earned_course_points}% · graded average ${grade.average_on_graded_work ?? "--"}%.`;
    } else if (grade.status === "impossible") {
        headline.textContent = `Target requires ${grade.required}% on remaining work.`;
        detail.textContent = "The selected target is not currently reachable without extra credit or a grading change.";
    } else {
        const shortBy = Number(grade.target) - Number(grade.earned_course_points);
        headline.textContent = `Final result: ${grade.earned_course_points}% (target ${grade.target}%).`;
        detail.textContent = `Every assessment is graded, so there is nothing left to calculate. The target was missed by ${Math.round(shortBy * 100) / 100} points.`;
    }

    result.append(headline, detail);
}


function showCoursesLoading() {
    document.querySelector("#coursesLoading").hidden = false;
    document.querySelector("#coursesError").hidden = true;
    document.querySelector("#courseGrid").hidden = true;
}


function showCoursesError(message) {
    document.querySelector("#coursesLoading").hidden = true;
    const error = document.querySelector("#coursesError");
    error.textContent = message;
    error.hidden = false;
}
