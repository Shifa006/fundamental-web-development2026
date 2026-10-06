document.addEventListener("DOMContentLoaded", () => {
    initTaskActions();
});

let editingTaskId = null;
let taskOptions = {
    subjects: [],
    projects: [],
};


async function initTaskActions() {
    document.querySelector("#addTaskButton")?.addEventListener("click", () => {
        openCreateTask();
    });

    document.querySelector("#taskForm")?.addEventListener("submit", submitTaskForm);
    document.querySelector("#taskArea")?.addEventListener("change", updateTaskFormRules);
    document.querySelector("#taskKind")?.addEventListener("change", updateTaskFormRules);
    document.querySelector("#taskProject")?.addEventListener("change", syncProjectSubject);

    document.addEventListener("planit:options-changed", async () => {
        await loadTaskOptions();
    });

    try {
        await loadTaskOptions();
    } catch (error) {
        console.error(error);
    }
}


async function loadTaskOptions() {
    taskOptions = await window.PlanitAPI.get("/api/task-options/");
    renderTaskOptions();
    return taskOptions;
}


function renderTaskOptions() {
    const subjectSelect = document.querySelector("#taskSubject");
    const projectSelect = document.querySelector("#taskProject");

    if (!subjectSelect || !projectSelect) {
        return;
    }

    subjectSelect.replaceChildren();
    projectSelect.replaceChildren();

    const noSubject = document.createElement("option");
    noSubject.value = "";
    noSubject.textContent = "No subject";
    subjectSelect.append(noSubject);

    taskOptions.subjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = subject.id;
        option.textContent = subject.code
            ? `${subject.code} — ${subject.name}`
            : subject.name;
        subjectSelect.append(option);
    });

    const noProject = document.createElement("option");
    noProject.value = "";
    noProject.textContent = "No project";
    projectSelect.append(noProject);

    taskOptions.projects.forEach((project) => {
        const option = document.createElement("option");
        option.value = project.id;
        option.textContent = project.title;
        option.dataset.subjectId = project.subject?.id ?? "";
        projectSelect.append(option);
    });
}


function getDefaultArea() {
    const active = document.querySelector("[data-area].is-active");
    if (active?.dataset.area && active.dataset.area !== "all") {
        return active.dataset.area;
    }
    return "academic";
}


function getDefaultDueDate() {
    return document.body.dataset.page === "today"
        ? document.body.dataset.today || ""
        : "";
}


function resetTaskForm() {
    const form = document.querySelector("#taskForm");
    form.reset();

    document.querySelector("#taskArea").value = getDefaultArea();
    document.querySelector("#taskKind").value = "general";
    document.querySelector("#taskPriority").value = "normal";
    document.querySelector("#taskDueDate").value = getDefaultDueDate();
    document.querySelector("#taskFormError").hidden = true;
    document.querySelector("#taskMoreOptions").open = false;
    updateTaskFormRules();
}


async function openCreateTask(overrides = {}) {
    editingTaskId = null;
    await loadTaskOptions();
    resetTaskForm();

    document.querySelector("#taskModalTitle").textContent = "Add task";
    document.querySelector("#taskSubmitButton").textContent = "Add task";

    if (overrides.area) {
        document.querySelector("#taskArea").value = overrides.area;
    }
    if (overrides.subjectId) {
        document.querySelector("#taskSubject").value = String(overrides.subjectId);
    }
    if (overrides.projectId) {
        document.querySelector("#taskProject").value = String(overrides.projectId);
        syncProjectSubject();
    }
    if (overrides.dueDate) {
        document.querySelector("#taskDueDate").value = overrides.dueDate;
    }

    updateTaskFormRules();
    showTaskModal();
}


async function openEditTask(task) {
    editingTaskId = task.id;
    await loadTaskOptions();
    resetTaskForm();

    document.querySelector("#taskModalTitle").textContent = "Edit task";
    document.querySelector("#taskSubmitButton").textContent = "Save changes";
    document.querySelector("#taskTitle").value = task.title;
    document.querySelector("#taskDescription").value = task.description || "";
    document.querySelector("#taskArea").value = task.area;
    document.querySelector("#taskKind").value = task.kind;
    document.querySelector("#taskPriority").value = task.priority;
    document.querySelector("#taskDueDate").value = task.due_date || "";
    document.querySelector("#taskSubject").value = task.subject?.id || "";
    document.querySelector("#taskProject").value = task.project?.id || "";
    document.querySelector("#taskMoreOptions").open = true;

    updateTaskFormRules();
    showTaskModal();
}


function showTaskModal() {
    const modalElement = document.querySelector("#taskModal");
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();

    modalElement.addEventListener(
        "shown.bs.modal",
        () => document.querySelector("#taskTitle")?.focus(),
        { once: true },
    );
}


function hideTaskModal() {
    const modal = bootstrap.Modal.getInstance(document.querySelector("#taskModal"));
    modal?.hide();
}


function updateTaskFormRules() {
    const area = document.querySelector("#taskArea")?.value;
    const kind = document.querySelector("#taskKind");
    const subject = document.querySelector("#taskSubject");
    const project = document.querySelector("#taskProject");
    const dueDate = document.querySelector("#taskDueDate");

    if (!kind || !subject || !project || !dueDate) {
        return;
    }

    const personal = area === "personal";

    Array.from(kind.options).forEach((option) => {
        option.disabled = personal && option.value !== "general";
    });

    if (personal) {
        kind.value = "general";
        subject.value = "";
        project.value = "";
    }

    subject.disabled = personal;
    project.disabled = personal;
    dueDate.required = kind.value === "exam";
}


function syncProjectSubject() {
    const projectSelect = document.querySelector("#taskProject");
    const selected = projectSelect?.selectedOptions[0];
    const subjectId = selected?.dataset.subjectId;

    if (subjectId) {
        document.querySelector("#taskSubject").value = subjectId;
    }
}


function buildTaskPayload() {
    return {
        title: document.querySelector("#taskTitle").value,
        description: document.querySelector("#taskDescription").value,
        area: document.querySelector("#taskArea").value,
        kind: document.querySelector("#taskKind").value,
        priority: document.querySelector("#taskPriority").value,
        due_date: document.querySelector("#taskDueDate").value || null,
        subject_id: document.querySelector("#taskSubject").value || null,
        project_id: document.querySelector("#taskProject").value || null,
    };
}


async function submitTaskForm(event) {
    event.preventDefault();

    const errorBox = document.querySelector("#taskFormError");
    const submit = document.querySelector("#taskSubmitButton");
    errorBox.hidden = true;
    submit.disabled = true;

    try {
        const payload = buildTaskPayload();

        if (editingTaskId) {
            await window.PlanitAPI.patch(`/api/tasks/${editingTaskId}/`, payload);
            window.PlanitUtils.showToast("Task updated.");
        } else {
            await window.PlanitAPI.post("/api/tasks/", payload);
            window.PlanitUtils.showToast("Task added.");
        }

        hideTaskModal();
        notifyTasksChanged();
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
    } finally {
        submit.disabled = false;
    }
}


async function toggleCompleted(task) {
    await window.PlanitAPI.patch(`/api/tasks/${task.id}/`, {
        completed: !task.completed,
    });
    window.PlanitUtils.showToast(task.completed ? "Task reopened." : "Task completed.");
    notifyTasksChanged();
}


async function deleteTask(task) {
    const confirmed = window.confirm(`Delete "${task.title}"?`);
    if (!confirmed) {
        return;
    }

    await window.PlanitAPI.delete(`/api/tasks/${task.id}/`);
    window.PlanitUtils.showToast("Task deleted.");
    notifyTasksChanged();
}


function notifyTasksChanged() {
    document.dispatchEvent(new CustomEvent("planit:tasks-changed"));
}


window.PlanitTasks = {
    openCreate: openCreateTask,
    openEdit: openEditTask,
    toggleCompleted,
    delete: deleteTask,
    reloadOptions: loadTaskOptions,
};
