document.addEventListener("DOMContentLoaded", () => {
    initProjectsPage();
});

let projects = [];
let selectedProject = null;
let editingProjectId = null;
let projectSubjects = [];


async function initProjectsPage() {
    document.querySelector("#addProjectButton")?.addEventListener("click", openCreateProject);
    document.querySelector("#projectForm")?.addEventListener("submit", submitProjectForm);
    document.querySelector("#editProjectButton")?.addEventListener("click", () => {
        if (selectedProject) {
            openEditProject(selectedProject);
        }
    });
    document.querySelector("#deleteProjectButton")?.addEventListener("click", deleteSelectedProject);
    document.querySelector("#projectAddTaskButton")?.addEventListener("click", () => {
        if (selectedProject) {
            window.PlanitTasks.openCreate({
                area: "academic",
                projectId: selectedProject.id,
                subjectId: selectedProject.subject?.id,
            });
        }
    });

    document.addEventListener("planit:tasks-changed", async () => {
        await loadProjects();
        if (selectedProject) {
            await loadProjectDetail(selectedProject.id);
        }
    });

    await Promise.all([
        loadProjectSubjects(),
        loadProjects(),
    ]);
}


async function loadProjectSubjects() {
    try {
        const data = await window.PlanitAPI.get("/api/subjects/");
        projectSubjects = data.subjects;
        renderProjectSubjectOptions();
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


function renderProjectSubjectOptions() {
    const select = document.querySelector("#projectSubject");
    if (!select) {
        return;
    }

    const previous = select.value;
    select.replaceChildren();

    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "No subject";
    select.append(empty);

    projectSubjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = subject.id;
        option.textContent = subject.code
            ? `${subject.code} — ${subject.name}`
            : subject.name;
        select.append(option);
    });

    select.value = previous;
}


async function loadProjects() {
    showProjectsLoading();

    try {
        const data = await window.PlanitAPI.get("/api/projects/");
        projects = data.projects;
        renderProjects();
        document.querySelector("#projectsLoading").hidden = true;
        document.querySelector("#projectGrid").hidden = false;
    } catch (error) {
        showProjectsError(error.message);
    }
}


function renderProjects() {
    const grid = document.querySelector("#projectGrid");
    grid.replaceChildren();

    if (!projects.length) {
        grid.append(window.PlanitUtils.emptyMessage("No projects yet. Add the first project to start tracking progress."));
        return;
    }

    projects.forEach((project, index) => {
        const article = document.createElement("article");
        article.className = `project-card project-${(index % 3) + 1} reveal`;

        if (index < 2) {
            const tape = document.createElement("div");
            tape.className = `tape ${index % 2 ? "alternate" : ""}`;
            tape.setAttribute("aria-hidden", "true");
            article.append(tape);
        }

        const header = document.createElement("header");
        const number = document.createElement("span");
        number.className = "project-index";
        number.textContent = String(index + 1).padStart(2, "0");
        const due = document.createElement("span");
        due.className = "project-date";
        due.textContent = project.due_date
            ? window.PlanitUtils.formatDate(project.due_date, { month: "short", day: "numeric", year: undefined }).toUpperCase()
            : "NO DATE";
        header.append(number, due);

        const titleWrap = document.createElement("div");
        titleWrap.className = "project-title";
        const label = document.createElement("span");
        label.className = "tiny-label";
        label.textContent = project.subject?.code || project.subject?.name || "PROJECT";
        const title = document.createElement("h2");
        title.textContent = project.title;
        titleWrap.append(label, title);

        const progressWrap = document.createElement("div");
        progressWrap.className = "project-progress";
        const percentWrap = document.createElement("div");
        percentWrap.className = "project-percent";
        const percent = document.createElement("strong");
        percent.textContent = project.progress.percent === null ? "--" : `${project.progress.percent}%`;
        const text = document.createElement("span");
        text.textContent = "complete";
        percentWrap.append(percent, text);

        const track = document.createElement("div");
        track.className = "progress-track";
        const bar = document.createElement("span");
        bar.style.width = `${project.progress.percent ?? 0}%`;
        track.append(bar);
        progressWrap.append(percentWrap, track);

        const footer = document.createElement("footer");
        const tasks = document.createElement("span");
        tasks.textContent = `${project.progress.completed} / ${project.progress.total} tasks`;
        const open = document.createElement("button");
        open.type = "button";
        open.className = "project-open-button";
        open.textContent = "Open project";
        open.addEventListener("click", () => loadProjectDetail(project.id));
        footer.append(tasks, open);

        article.append(header, titleWrap, progressWrap, footer);
        grid.append(article);
    });
}


async function loadProjectDetail(projectId) {
    try {
        const data = await window.PlanitAPI.get(`/api/projects/${projectId}/`);
        selectedProject = data.project;
        renderProjectDetail(selectedProject);
        document.querySelector("#projectDetail").hidden = false;
        document.querySelector("#projectDetail").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


function renderProjectDetail(project) {
    window.PlanitUtils.setText(
        "#projectDetailSubject",
        project.subject?.code || project.subject?.name || "PROJECT",
    );
    window.PlanitUtils.setText("#projectDetailTitle", project.title);
    window.PlanitUtils.setText(
        "#projectDetailDescription",
        project.description || "No description yet.",
    );
    window.PlanitUtils.setText(
        "#projectDetailProgress",
        project.progress.percent === null ? "--" : `${project.progress.percent}%`,
    );
    window.PlanitUtils.setText(
        "#projectDetailProgressMeta",
        project.progress.total === 0
            ? "No project tasks yet"
            : `${project.progress.completed} of ${project.progress.total} completed`,
    );
    window.PlanitUtils.setText(
        "#projectDetailDue",
        project.due_date
            ? window.PlanitUtils.formatDate(project.due_date, { month: "short", day: "numeric", year: undefined })
            : "No date",
    );

    renderProjectTasks(project.tasks);
}


function renderProjectTasks(projectTasks) {
    const list = document.querySelector("#projectTaskList");
    list.replaceChildren();

    if (!projectTasks.length) {
        list.append(window.PlanitUtils.emptyMessage("Add the first project task to start tracking progress."));
        return;
    }

    projectTasks.forEach((task) => {
        const row = document.createElement("div");
        row.className = "mini-list-row project-task-row";

        const check = document.createElement("button");
        check.type = "button";
        check.className = "check-box";
        if (task.completed) {
            check.classList.add("is-checked");
        }
        check.setAttribute(
            "aria-label",
            task.completed ? `Uncomplete ${task.title}` : `Complete ${task.title}`,
        );
        check.addEventListener("click", async () => {
            check.disabled = true;
            try {
                await window.PlanitTasks.toggleCompleted(task);
            } catch (error) {
                check.disabled = false;
                window.PlanitUtils.showToast(error.message, "error");
            }
        });

        const copy = document.createElement("span");
        const title = document.createElement("strong");
        title.textContent = task.title;
        const meta = document.createElement("small");
        meta.textContent = window.PlanitUtils.taskStatusLabel(task);
        copy.append(title, meta);

        const edit = document.createElement("button");
        edit.type = "button";
        edit.className = "text-action";
        edit.textContent = "Edit";
        edit.addEventListener("click", () => window.PlanitTasks.openEdit(task));

        row.append(check, copy, edit);
        list.append(row);
    });
}


async function openCreateProject() {
    editingProjectId = null;
    await loadProjectSubjects();
    document.querySelector("#projectForm").reset();
    document.querySelector("#projectFormError").hidden = true;
    window.PlanitUtils.setText("#projectModalTitle", "Add project");
    window.PlanitUtils.setText("#projectSubmitButton", "Save project");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#projectModal")).show();
}


async function openEditProject(project) {
    editingProjectId = project.id;
    await loadProjectSubjects();
    document.querySelector("#projectFormError").hidden = true;
    document.querySelector("#projectTitle").value = project.title;
    document.querySelector("#projectDescription").value = project.description || "";
    document.querySelector("#projectDueDate").value = project.due_date || "";
    document.querySelector("#projectSubject").value = project.subject?.id || "";
    window.PlanitUtils.setText("#projectModalTitle", "Edit project");
    window.PlanitUtils.setText("#projectSubmitButton", "Save changes");
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#projectModal")).show();
}


async function submitProjectForm(event) {
    event.preventDefault();

    const errorBox = document.querySelector("#projectFormError");
    const submit = document.querySelector("#projectSubmitButton");
    errorBox.hidden = true;
    submit.disabled = true;

    const payload = {
        title: document.querySelector("#projectTitle").value,
        description: document.querySelector("#projectDescription").value,
        due_date: document.querySelector("#projectDueDate").value || null,
        subject_id: document.querySelector("#projectSubject").value || null,
    };

    try {
        const response = editingProjectId
            ? await window.PlanitAPI.patch(`/api/projects/${editingProjectId}/`, payload)
            : await window.PlanitAPI.post("/api/projects/", payload);

        bootstrap.Modal.getInstance(document.querySelector("#projectModal"))?.hide();
        selectedProject = response.project;
        window.PlanitUtils.showToast(editingProjectId ? "Project updated." : "Project added.");
        document.dispatchEvent(new CustomEvent("planit:options-changed"));
        await loadProjects();
        await loadProjectDetail(response.project.id);
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
    } finally {
        submit.disabled = false;
    }
}


async function deleteSelectedProject() {
    if (!selectedProject) {
        return;
    }

    const impact = selectedProject.delete_impact;
    const message = impact
        ? `Delete "${selectedProject.title}"?\n${impact.tasks_detached} linked tasks will be kept and detached.`
        : `Delete "${selectedProject.title}"?`;

    if (!window.confirm(message)) {
        return;
    }

    try {
        await window.PlanitAPI.delete(`/api/projects/${selectedProject.id}/`);
        selectedProject = null;
        document.querySelector("#projectDetail").hidden = true;
        document.dispatchEvent(new CustomEvent("planit:options-changed"));
        document.dispatchEvent(new CustomEvent("planit:tasks-changed"));
        window.PlanitUtils.showToast("Project deleted.");
        await loadProjects();
    } catch (error) {
        window.PlanitUtils.showToast(error.message, "error");
    }
}


function showProjectsLoading() {
    document.querySelector("#projectsLoading").hidden = false;
    document.querySelector("#projectsError").hidden = true;
    document.querySelector("#projectGrid").hidden = true;
}


function showProjectsError(message) {
    document.querySelector("#projectsLoading").hidden = true;
    const error = document.querySelector("#projectsError");
    error.textContent = message;
    error.hidden = false;
}
