document.addEventListener("DOMContentLoaded", () => {
    initTasksPage();
});

let tasks = [];
let selectedArea = "all";
let selectedView = "all";
let searchQuery = "";
let selectedPriority = "all";
let selectedStatus = "all";
let selectedSubject = "all";
let selectedSort = "attention";


async function initTasksPage() {
    initAreaButtons();
    initViewButtons();
    initSearch();
    initSelectFilters();

    document.addEventListener("planit:exam-mode-change", async () => {
        if (selectedView === "week") {
            await loadWeek();
        } else {
            renderFilteredTasks();
        }
    });

    document.addEventListener("planit:tasks-changed", loadTasks);
    document.addEventListener("planit:options-changed", populateSubjectFilter);

    await loadTasks();
}


async function loadTasks() {
    showTasksLoading();

    try {
        const data = await window.PlanitAPI.get("/api/tasks/");
        tasks = data.tasks;
        await populateSubjectFilter();

        if (selectedView === "week") {
            await loadWeek();
        } else {
            renderFilteredTasks();
            showAllTasks();
        }
    } catch (error) {
        showTasksError(error.message);
    }
}


async function populateSubjectFilter() {
    const select = document.querySelector("#subjectFilter");
    if (!select) {
        return;
    }

    let subjects = [];

    try {
        const data = await window.PlanitAPI.get("/api/task-options/");
        subjects = data.subjects;
    } catch {
        const byId = new Map();
        tasks.forEach((task) => {
            if (task.subject) {
                byId.set(task.subject.id, task.subject);
            }
        });
        subjects = Array.from(byId.values());
    }

    const previous = selectedSubject;
    select.replaceChildren();

    const all = document.createElement("option");
    all.value = "all";
    all.textContent = "All subjects";
    select.append(all);

    subjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = String(subject.id);
        option.textContent = subject.code
            ? `${subject.code} — ${subject.name}`
            : subject.name;
        select.append(option);
    });

    const stillExists = Array.from(select.options).some((option) => option.value === previous);
    selectedSubject = stillExists ? previous : "all";
    select.value = selectedSubject;
}


function initAreaButtons() {
    document.querySelectorAll(".filter-button[data-area]").forEach((button) => {
        button.addEventListener("click", async () => {
            document.querySelectorAll(".filter-button[data-area]").forEach((item) => {
                item.classList.remove("is-active");
            });

            button.classList.add("is-active");
            selectedArea = button.dataset.area;

            if (selectedView === "week") {
                await loadWeek();
            } else {
                renderFilteredTasks();
            }
        });
    });
}


function initViewButtons() {
    document.querySelectorAll(".view-tab[data-view]").forEach((button) => {
        button.addEventListener("click", async () => {
            document.querySelectorAll(".view-tab[data-view]").forEach((item) => {
                item.classList.remove("is-active");
            });

            button.classList.add("is-active");
            selectedView = button.dataset.view;

            if (selectedView === "week") {
                await loadWeek();
            } else {
                renderFilteredTasks();
                showAllTasks();
            }
        });
    });
}


function initSearch() {
    document.querySelector("#taskSearch")?.addEventListener("input", (event) => {
        searchQuery = event.target.value.trim().toLowerCase();
        refreshCurrentView();
    });
}


function initSelectFilters() {
    document.querySelector("#priorityFilter")?.addEventListener("change", (event) => {
        selectedPriority = event.target.value;
        refreshCurrentView();
    });

    document.querySelector("#statusFilter")?.addEventListener("change", (event) => {
        selectedStatus = event.target.value;
        refreshCurrentView();
    });

    document.querySelector("#subjectFilter")?.addEventListener("change", (event) => {
        selectedSubject = event.target.value;
        refreshCurrentView();
    });

    document.querySelector("#sortFilter")?.addEventListener("change", (event) => {
        selectedSort = event.target.value;
        refreshCurrentView();
    });
}


async function refreshCurrentView() {
    if (selectedView === "week") {
        await loadWeek();
    } else {
        renderFilteredTasks();
    }
}


function matchesClientFilters(task) {
    const examMode = window.PlanitUI.getExamMode();

    const areaMatches = selectedArea === "all" || task.area === selectedArea;
    const examModeMatches = !examMode || task.exam_mode_visible;
    const searchMatches = !searchQuery || task.title.toLowerCase().includes(searchQuery);
    const priorityMatches = selectedPriority === "all" || task.priority === selectedPriority;
    const subjectMatches = selectedSubject === "all" || String(task.subject?.id ?? "") === selectedSubject;

    let statusMatches = true;
    if (selectedStatus === "pending") {
        statusMatches = ["overdue", "today", "upcoming", "no_date"].includes(task.status);
    } else if (selectedStatus !== "all") {
        statusMatches = task.status === selectedStatus;
    }

    return (
        areaMatches
        && examModeMatches
        && searchMatches
        && priorityMatches
        && subjectMatches
        && statusMatches
    );
}


function getFilteredTasks() {
    return tasks.filter(matchesClientFilters).sort(taskSortComparator);
}


function taskSortComparator(a, b) {
    if (selectedSort === "priority") {
        return a.priority_rank - b.priority_rank || a.attention_rank - b.attention_rank;
    }

    if (selectedSort === "due") {
        if (!a.due_date && !b.due_date) {
            return a.attention_rank - b.attention_rank;
        }
        if (!a.due_date) {
            return 1;
        }
        if (!b.due_date) {
            return -1;
        }
        return a.due_date.localeCompare(b.due_date) || a.attention_rank - b.attention_rank;
    }

    return a.attention_rank - b.attention_rank;
}


function renderFilteredTasks() {
    const list = document.querySelector("#archiveTaskList");
    if (!list) {
        return;
    }

    list.replaceChildren();
    const filtered = getFilteredTasks();
    renderActiveCount(filtered);

    window.PlanitUtils.setText(
        "#taskListCount",
        `${filtered.length} ${filtered.length === 1 ? "ITEM" : "ITEMS"}`,
    );

    if (!filtered.length) {
        list.append(window.PlanitUtils.emptyMessage("No tasks match these filters."));
        return;
    }

    const fragment = document.createDocumentFragment();
    filtered.forEach((task) => fragment.append(createArchiveTask(task)));
    list.append(fragment);
}


function createArchiveTask(task) {
    const article = document.createElement("article");
    article.className = "archive-task";
    if (task.completed) {
        article.classList.add("is-complete");
    }

    const check = document.createElement("button");
    check.type = "button";
    check.className = "check-box";
    check.setAttribute(
        "aria-label",
        task.completed ? `Uncomplete ${task.title}` : `Complete ${task.title}`,
    );
    if (task.completed) {
        check.classList.add("is-checked");
    }

    check.addEventListener("click", async () => {
        check.disabled = true;
        try {
            await window.PlanitTasks.toggleCompleted(task);
        } catch (error) {
            check.disabled = false;
            window.PlanitUtils.showToast(error.message, "error");
        }
    });

    const body = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = task.title;
    const detail = document.createElement("span");
    detail.textContent = window.PlanitUtils.taskContext(task);
    body.append(title, detail);

    const status = document.createElement("span");
    status.className = `task-status ${window.PlanitUtils.statusClass(task)}`;
    status.textContent = window.PlanitUtils.taskStatusLabel(task);

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "text-action";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", () => window.PlanitTasks.openEdit(task));

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "text-action danger-action";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", async () => {
        try {
            await window.PlanitTasks.delete(task);
        } catch (error) {
            window.PlanitUtils.showToast(error.message, "error");
        }
    });

    actions.append(editButton, deleteButton);
    article.append(check, body, status, actions);
    return article;
}


async function loadWeek() {
    showTasksLoading();

    const params = new URLSearchParams({
        area: selectedArea,
        exam_mode: window.PlanitUI.getExamMode() ? "1" : "0",
    });

    try {
        const data = await window.PlanitAPI.get(`/api/week/?${params}`);
        renderWeek(data.days);
        hideTasksLoading();
        document.querySelector("#allTasksView").hidden = true;
        document.querySelector("#weekTasksView").hidden = false;
    } catch (error) {
        showTasksError(error.message);
    }
}


function renderWeek(days) {
    const grid = document.querySelector("#weekGrid");
    grid.replaceChildren();

    days.forEach((day) => {
        const column = document.createElement("article");
        column.className = "week-column";

        if (day.date === document.body.dataset.today) {
            column.classList.add("is-today");
        }

        const header = document.createElement("header");
        const name = document.createElement("span");
        name.textContent = day.weekday.slice(0, 3).toUpperCase();
        const number = document.createElement("strong");
        number.textContent = day.date.slice(-2);
        header.append(name, number);
        column.append(header);

        const visibleTasks = day.tasks.filter(matchesClientFilters);

        if (!visibleTasks.length) {
            const empty = document.createElement("p");
            empty.className = "empty-day";
            empty.textContent = "No tasks";
            column.append(empty);
        }

        visibleTasks.forEach((task) => {
            const card = document.createElement("button");
            card.type = "button";
            card.className = `week-task ${window.PlanitUtils.kindClass(task.kind)}`;
            if (task.status === "past_exam") {
                card.classList.add("is-past");
            }

            const title = document.createElement("strong");
            title.textContent = task.title;
            const detail = document.createElement("span");
            detail.textContent = window.PlanitUtils.taskContext(task);
            card.append(title, detail);
            card.addEventListener("click", () => window.PlanitTasks.openEdit(task));
            column.append(card);
        });

        grid.append(column);
    });
}


function renderActiveCount(filteredTasks) {
    const count = filteredTasks.filter(
        (task) => !task.completed && task.status !== "past_exam",
    ).length;
    window.PlanitUtils.setText("#activeTaskCount", window.PlanitUtils.formatCount(count));
}


function showTasksLoading() {
    document.querySelector("#tasksLoading").hidden = false;
    document.querySelector("#tasksError").hidden = true;
    document.querySelector("#allTasksView").hidden = true;
    document.querySelector("#weekTasksView").hidden = true;
}


function hideTasksLoading() {
    document.querySelector("#tasksLoading").hidden = true;
}


function showAllTasks() {
    hideTasksLoading();
    document.querySelector("#tasksError").hidden = true;
    document.querySelector("#weekTasksView").hidden = true;
    document.querySelector("#allTasksView").hidden = false;
}


function showTasksError(message) {
    hideTasksLoading();
    const error = document.querySelector("#tasksError");
    error.textContent = message;
    error.hidden = false;
}
