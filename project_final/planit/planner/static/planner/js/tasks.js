document.addEventListener("DOMContentLoaded", () => {
    initTasksPage();
});

let tasks = [];
let weekDays = [];
let weekMeta = null;
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
        if (isCalendarView()) {
            await loadWeek();
        } else {
            renderFilteredTasks();
        }
    });

    document.addEventListener("planit:tasks-changed", loadTasks);

    document.addEventListener("planit:options-changed", async () => {
        await populateSubjectFilter();
        refreshCurrentView();
    });

    await loadTasks();
}


async function loadTasks() {
    showTasksLoading();

    try {
        const data = await window.PlanitAPI.get("/api/tasks/");
        tasks = data.tasks;
        await populateSubjectFilter();

        if (isCalendarView()) {
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

    const stillExists = Array.from(select.options).some(
        (option) => option.value === previous,
    );
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

            if (isCalendarView()) {
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

            if (isCalendarView()) {
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


function refreshCurrentView() {
    if (selectedView === "month") {
        window.PlanitMonth.rerender();
    } else if (isCalendarView()) {
        renderWeek(weekDays);
    } else {
        renderFilteredTasks();
    }
}


function matchesClientFilters(task, { preservePastExam = false } = {}) {
    const examMode = window.PlanitUI.getExamMode();

    const areaMatches = selectedArea === "all" || task.area === selectedArea;
    const examModeMatches = (
        !examMode
        || task.exam_mode_visible
        || (preservePastExam && task.status === "past_exam")
    );

    const searchableText = [
        task.title,
        task.description,
        task.subject?.name,
        task.subject?.code,
        task.project?.title,
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

    const searchMatches = !searchQuery || searchableText.includes(searchQuery);
    const priorityMatches = selectedPriority === "all" || task.priority === selectedPriority;
    const subjectMatches = (
        selectedSubject === "all"
        || String(task.subject?.id ?? "") === selectedSubject
    );

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
    return tasks
        .filter((task) => matchesClientFilters(task))
        .sort(taskSortComparator);
}


function attentionRank(task) {
    return Number.isFinite(task.attention_rank)
        ? task.attention_rank
        : Number.MAX_SAFE_INTEGER;
}


function taskSortComparator(a, b) {
    if (selectedSort === "priority") {
        return a.priority_rank - b.priority_rank || attentionRank(a) - attentionRank(b);
    }

    if (selectedSort === "due") {
        if (!a.due_date && !b.due_date) {
            return attentionRank(a) - attentionRank(b);
        }
        if (!a.due_date) {
            return 1;
        }
        if (!b.due_date) {
            return -1;
        }
        return a.due_date.localeCompare(b.due_date) || attentionRank(a) - attentionRank(b);
    }

    return attentionRank(a) - attentionRank(b);
}


function addTaskStateClasses(element, task) {
    element.classList.add(`kind-${task.kind}`, `priority-${task.priority}`, `status-${task.status}`);
    element.classList.add(task.area === "personal" ? "area-personal" : "area-academic");

    if (task.completed) {
        element.classList.add("is-complete");
    }
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
    article.className = "archive-task quest-inventory-row";
    addTaskStateClasses(article, task);

    const check = document.createElement("button");
    check.type = "button";
    check.className = "check-box";
    check.setAttribute(
        "aria-label",
        task.completed ? `Mark ${task.title} as incomplete` : `Complete ${task.title}`,
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
    body.className = "archive-task-copy";

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

    const duplicateButton = document.createElement("button");
    duplicateButton.type = "button";
    duplicateButton.className = "text-action";
    duplicateButton.textContent = "Duplicate";
    duplicateButton.setAttribute("aria-label", `Duplicate ${task.title} for today`);
    duplicateButton.addEventListener("click", async () => {
        try {
            await window.PlanitTasks.duplicate(task);
        } catch (error) {
            window.PlanitUtils.showToast(error.message, "error");
        }
    });

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

    actions.append(editButton, duplicateButton, deleteButton);
    article.append(check, body, status, actions);
    return article;
}


function isCalendarView() {
    return selectedView === "week" || selectedView === "month";
}


async function loadWeek() {
    if (selectedView === "month") {
        await window.PlanitMonth.load({
            area: selectedArea,
            examMode: window.PlanitUI.getExamMode(),
            onLoading: showTasksLoading,
            onReady: hideTasksLoading,
            onError: showTasksError,
            matches: (task) => matchesClientFilters(task, { preservePastExam: true }),
            sorter: taskSortComparator,
            makeRow: createArchiveTask,
        });
        return;
    }

    showTasksLoading();

    const params = new URLSearchParams({
        area: selectedArea,
        exam_mode: window.PlanitUI.getExamMode() ? "1" : "0",
    });

    try {
        const data = await window.PlanitAPI.get(`/api/week/?${params}`);
        weekDays = data.days;
        weekMeta = data.meta;
        renderWeekRange(weekMeta);
        renderWeek(weekDays);
        hideTasksLoading();
        document.querySelector("#tasksError").hidden = true;
        document.querySelector("#allTasksView").hidden = true;
        document.querySelector("#weekTasksView").hidden = false;
    } catch (error) {
        showTasksError(error.message);
    }
}


function renderWeekRange(meta) {
    if (!meta?.week_start || !meta?.week_end) {
        return;
    }

    const start = window.PlanitUtils.parseLocalDate(meta.week_start);
    const end = window.PlanitUtils.parseLocalDate(meta.week_end);

    const startMonth = new Intl.DateTimeFormat("en-US", { month: "short" }).format(start);
    const endMonth = new Intl.DateTimeFormat("en-US", { month: "short" }).format(end);

    const label = start.getMonth() === end.getMonth()
        ? `${start.getDate()}–${end.getDate()} ${startMonth}`
        : `${start.getDate()} ${startMonth} – ${end.getDate()} ${endMonth}`;

    window.PlanitUtils.setText("#weekRange", label);
}


function renderWeek(days) {
    const grid = document.querySelector("#weekGrid");
    if (!grid) {
        return;
    }

    grid.replaceChildren();
    const allVisibleTasks = [];

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
        number.textContent = String(Number(day.date.slice(-2)));
        header.append(name, number);
        column.append(header);

        const visibleTasks = day.tasks
            .filter((task) => matchesClientFilters(task, { preservePastExam: true }))
            .sort(taskSortComparator);

        allVisibleTasks.push(...visibleTasks);

        if (!visibleTasks.length) {
            const empty = document.createElement("p");
            empty.className = "empty-day";
            empty.textContent = "No tasks";
            column.append(empty);
        }

        visibleTasks.forEach((task) => {
            const card = document.createElement("button");
            card.type = "button";
            card.className = "week-task";
            addTaskStateClasses(card, task);

            if (task.status === "past_exam") {
                card.classList.add("is-past");
            }

            const meta = document.createElement("span");
            meta.className = "week-task-meta";
            meta.textContent = task.kind === "exam"
                ? "EXAM"
                : window.PlanitUtils.formatKind(task.kind).toUpperCase();

            const title = document.createElement("strong");
            title.textContent = task.title;

            const detail = document.createElement("span");
            detail.className = "week-task-detail";
            detail.textContent = window.PlanitUtils.taskContext(task);

            const status = document.createElement("small");
            status.className = "week-task-status";
            status.textContent = window.PlanitUtils.taskStatusLabel(task);

            card.append(meta, title, detail, status);
            card.addEventListener("click", () => window.PlanitTasks.openEdit(task));
            column.append(card);
        });

        grid.append(column);
    });

    renderActiveCount(allVisibleTasks);
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
    document.querySelector("#monthTasksView").hidden = true;
}


function hideTasksLoading() {
    document.querySelector("#tasksLoading").hidden = true;
}


function showAllTasks() {
    hideTasksLoading();
    document.querySelector("#tasksError").hidden = true;
    document.querySelector("#weekTasksView").hidden = true;
    document.querySelector("#monthTasksView").hidden = true;
    document.querySelector("#allTasksView").hidden = false;
}


function showTasksError(message) {
    hideTasksLoading();
    document.querySelector("#allTasksView").hidden = true;
    document.querySelector("#weekTasksView").hidden = true;
    document.querySelector("#monthTasksView").hidden = true;
    const error = document.querySelector("#tasksError");
    error.textContent = message;
    error.hidden = false;
}
