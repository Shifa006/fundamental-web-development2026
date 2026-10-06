document.addEventListener("DOMContentLoaded", () => {
    initTodayPage();
});

let selectedArea = "all";


async function initTodayPage() {
    initAreaFilters();

    document.addEventListener("planit:exam-mode-change", loadToday);
    document.addEventListener("planit:tasks-changed", loadToday);

    await loadToday();
}


function initAreaFilters() {
    document.querySelectorAll(".area-filter").forEach((button) => {
        button.addEventListener("click", async () => {
            document.querySelectorAll(".area-filter").forEach((item) => {
                item.classList.remove("is-active");
            });

            button.classList.add("is-active");
            selectedArea = button.dataset.area;
            await loadToday();
        });
    });
}


async function loadToday() {
    showLoading();

    const params = new URLSearchParams({
        area: selectedArea,
        exam_mode: window.PlanitUI.getExamMode() ? "1" : "0",
    });

    try {
        const data = await window.PlanitAPI.get(`/api/today/?${params}`);
        document.body.dataset.today = data.meta.today;
        renderToday(data);
        showContent();
    } catch (error) {
        showError(error.message);
    }
}


function renderToday(data) {
    renderDate(data.meta.today);
    renderProgress(data.progress);
    renderTaskList("#todayTaskList", data.today, "Nothing is due today.");
    renderTaskList("#overdueTaskList", data.overdue, "Nothing overdue.");

    window.PlanitUtils.setText("#todayCount", window.PlanitUtils.formatCount(data.today.length));
    window.PlanitUtils.setText("#overdueCount", window.PlanitUtils.formatCount(data.overdue.length));

    renderNextExam(data.next_exam);
    renderHiddenCount(data.hidden_by_exam_mode);
}


function renderDate(isoDate) {
    const date = window.PlanitUtils.parseLocalDate(isoDate);

    window.PlanitUtils.setText(
        "#todayDate",
        new Intl.DateTimeFormat("en-US", {
            weekday: "long",
            month: "long",
            day: "numeric",
        }).format(date),
    );

    window.PlanitUtils.setText(
        "#dateMonth",
        new Intl.DateTimeFormat("en-US", { month: "short" }).format(date).toUpperCase(),
    );
    window.PlanitUtils.setText("#dateNumber", String(date.getDate()).padStart(2, "0"));
    window.PlanitUtils.setText(
        "#dateWeekday",
        new Intl.DateTimeFormat("en-US", { weekday: "short" }).format(date).toUpperCase(),
    );

    renderCalendar(date);
}


function renderProgress(progress) {
    window.PlanitUtils.setText(
        "#progressCompleted",
        String(progress.completed).padStart(2, "0"),
    );
    window.PlanitUtils.setText(
        "#progressTotal",
        String(progress.total).padStart(2, "0"),
    );

    const percent = progress.percent ?? 0;
    const bar = document.querySelector("#todayProgressBar");
    if (bar) {
        bar.style.width = `${percent}%`;
    }

    window.PlanitUtils.setText(
        "#progressText",
        progress.percent === null ? "No tasks due today" : `${percent}% completed`,
    );
}


function renderTaskList(selector, tasks, emptyText) {
    const container = document.querySelector(selector);
    if (!container) {
        return;
    }

    container.replaceChildren();

    if (!tasks.length) {
        container.append(window.PlanitUtils.emptyMessage(emptyText));
        return;
    }

    const fragment = document.createDocumentFragment();
    tasks.forEach((task) => fragment.append(createTaskRow(task)));
    container.append(fragment);
}


function createTaskRow(task) {
    const article = document.createElement("article");
    article.className = "task-row";

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

    const copy = document.createElement("div");
    copy.className = "task-copy";

    const title = document.createElement("strong");
    title.textContent = task.title;

    const context = document.createElement("span");
    context.textContent = window.PlanitUtils.taskContext(task);

    copy.append(title, context);

    const kind = document.createElement("span");
    kind.className = `category-pill ${window.PlanitUtils.kindClass(task.kind)}`;
    kind.textContent = window.PlanitUtils.formatKind(task.kind);

    const status = document.createElement("span");
    status.className = "priority-text";
    if (task.priority === "urgent" || task.status === "overdue") {
        status.classList.add("urgent");
    }
    status.textContent = window.PlanitUtils.taskStatusLabel(task);

    article.append(check, copy, kind, status);
    return article;
}


function renderNextExam(exam) {
    const countdown = document.querySelector("#examCountdown");

    if (!exam) {
        window.PlanitUtils.setText("#nextExamTitle", "No upcoming exam");
        window.PlanitUtils.setText("#nextExamDate", "Your schedule is clear.");
        if (countdown) {
            countdown.hidden = true;
        }
        return;
    }

    window.PlanitUtils.setText("#nextExamTitle", exam.title);
    window.PlanitUtils.setText(
        "#nextExamDate",
        window.PlanitUtils.formatDate(exam.due_date, {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: undefined,
        }),
    );

    if (countdown) {
        countdown.hidden = false;
    }

    window.PlanitUtils.setText("#examDays", exam.days_left);
    window.PlanitUtils.setText("#examDaysLabel", exam.days_left === 1 ? "day" : "days");
}


function renderHiddenCount(count) {
    const element = document.querySelector("#examHiddenMessage");
    if (!element) {
        return;
    }

    if (!count) {
        element.hidden = true;
        return;
    }

    element.textContent = `${count} active item${count === 1 ? "" : "s"} hidden by Exam Mode.`;
    element.hidden = false;
}


function renderCalendar(date) {
    window.PlanitUtils.setText(
        "#calendarMonth",
        new Intl.DateTimeFormat("en-US", { month: "long" }).format(date),
    );
    window.PlanitUtils.setText("#calendarYear", date.getFullYear());

    const calendar = document.querySelector("#miniCalendar");
    if (!calendar) {
        return;
    }

    calendar.replaceChildren();

    ["M", "T", "W", "T", "F", "S", "S"].forEach((name) => {
        const label = document.createElement("span");
        label.className = "day-name";
        label.textContent = name;
        calendar.append(label);
    });

    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const mondayIndex = (firstDay.getDay() + 6) % 7;

    for (let i = 0; i < mondayIndex; i += 1) {
        calendar.append(document.createElement("span"));
    }

    for (let day = 1; day <= lastDay.getDate(); day += 1) {
        const cell = document.createElement("span");
        cell.textContent = day;

        if (day === date.getDate()) {
            cell.classList.add("current-day");
        }

        calendar.append(cell);
    }
}


function showLoading() {
    document.querySelector("#todayLoading").hidden = false;
    document.querySelector("#todayContent").hidden = true;
    document.querySelector("#todayError").hidden = true;
}


function showContent() {
    document.querySelector("#todayLoading").hidden = true;
    document.querySelector("#todayContent").hidden = false;
}


function showError(message) {
    document.querySelector("#todayLoading").hidden = true;
    document.querySelector("#todayContent").hidden = true;

    const error = document.querySelector("#todayError");
    error.textContent = message;
    error.hidden = false;
}
