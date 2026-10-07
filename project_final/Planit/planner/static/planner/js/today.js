document.addEventListener("DOMContentLoaded", () => {
    initTodayPage();
});

let selectedArea = "all";


async function initTodayPage() {
    initAreaFilters();
    renderGreeting();

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


function renderGreeting() {
    const greeting = document.querySelector("#todayGreeting");
    if (!greeting) {
        return;
    }

    const hour = new Date().getHours();
    if (hour < 12) {
        greeting.textContent = "Good morning";
    } else if (hour < 18) {
        greeting.textContent = "Good afternoon";
    } else {
        greeting.textContent = "Good evening";
    }
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
    renderTaskList("#todayTaskList", data.today, "No tasks due today. Tap + to add one.");
    renderTaskList("#overdueTaskList", data.overdue, "No overdue tasks. Nice work.");

    window.PlanitUtils.setText("#todayCount", window.PlanitUtils.formatCount(data.today.length));
    window.PlanitUtils.setText("#overdueCount", window.PlanitUtils.formatCount(data.overdue.length));

    renderTopFocus(data.top_focus);
    renderNextExam(data.next_exam);
    renderHiddenCount(data.hidden_by_exam_mode);
    renderExamSuggestion(data);
}


function renderExamSuggestion(data) {
    const box = document.querySelector("#examSuggestion");
    if (!box) {
        return;
    }

    const key = `planit-exam-suggest-${data.meta.today}`;
    let dismissed = false;
    try {
        dismissed = window.localStorage.getItem(key) === "1";
    } catch {
        dismissed = false;
    }

    const exam = data.next_exam;
    if (!data.suggest_exam_mode || dismissed || !exam) {
        box.hidden = true;
        return;
    }

    const days = exam.days_left;
    const when = days === 0 ? "today" : `in ${days} day${days === 1 ? "" : "s"}`;
    window.PlanitUtils.setText("#examSuggestionText", `${exam.title} is ${when}. Focus on what matters?`);
    box.hidden = false;

    document.querySelector("#examSuggestionOn").onclick = () => {
        window.PlanitUI.setExamMode(true);
        window.PlanitUI.updateExamModeControls();
        document.dispatchEvent(new CustomEvent("planit:exam-mode-change", { detail: { enabled: true } }));
        box.hidden = true;
    };
    document.querySelector("#examSuggestionDismiss").onclick = () => {
        try {
            window.localStorage.setItem(key, "1");
        } catch {
            /* storage unavailable: dismiss for this view only */
        }
        box.hidden = true;
    };
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
    window.PlanitUtils.setText("#progressCompleted", String(progress.completed));
    window.PlanitUtils.setText("#progressTotal", String(progress.total));

    const percent = progress.percent ?? 0;
    const roundedPercent = Math.round(percent);
    const bar = document.querySelector("#todayProgressBar");
    const ring = document.querySelector("#todayProgressRing");

    if (bar) {
        bar.style.width = `${percent}%`;
    }

    if (ring) {
        ring.style.setProperty("--progress", `${percent * 3.6}deg`);
    }

    window.PlanitUtils.setText("#progressPercent", `${roundedPercent}%`);

    let message = "No tasks due today";
    if (progress.percent !== null) {
        if (percent >= 100) {
            message = "All of today's tasks are done. Nice work.";
        } else if (percent >= 60) {
            message = "Almost there. Keep the streak going.";
        } else if (progress.completed > 0) {
            message = "Progress saved. Pick your next task.";
        } else {
            message = "Start with one small task.";
        }
    }

    window.PlanitUtils.setText("#progressText", message);
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


function addTaskStateClasses(element, task) {
    element.classList.add(`kind-${task.kind}`, `priority-${task.priority}`, `status-${task.status}`);

    if (task.area === "personal") {
        element.classList.add("area-personal");
    } else {
        element.classList.add("area-academic");
    }

    if (task.completed) {
        element.classList.add("is-complete");
    }
}


function createTaskRow(task) {
    const article = document.createElement("article");
    article.className = "task-row quest-row";
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
    status.className = `priority-text ${window.PlanitUtils.statusClass(task)}`;
    status.textContent = window.PlanitUtils.taskStatusLabel(task);

    article.append(check, copy, kind, status);
    return article;
}


function renderTopFocus(task) {
    const content = document.querySelector("#topFocusContent");
    const empty = document.querySelector("#topFocusEmpty");
    const card = document.querySelector(".top-focus-card");

    if (!content || !empty || !card) {
        return;
    }

    card.classList.remove(
        "kind-general",
        "kind-assignment",
        "kind-study",
        "kind-exam",
        "priority-urgent",
        "priority-normal",
        "priority-later",
        "status-overdue",
        "status-today",
        "status-upcoming",
        "status-no_date",
    );

    if (!task) {
        content.hidden = true;
        empty.hidden = false;
        return;
    }

    content.hidden = false;
    empty.hidden = true;
    addTaskStateClasses(card, task);

    window.PlanitUtils.setText("#topFocusTitle", task.title);
    window.PlanitUtils.setText(
        "#topFocusMeta",
        `${window.PlanitUtils.taskContext(task)} · ${window.PlanitUtils.taskStatusLabel(task)}`,
    );

    const score = Number(task.attention_score ?? 0);
    window.PlanitUtils.setText("#topFocusScore", score.toFixed(2));
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

    element.textContent = `${count} active task${count === 1 ? "" : "s"} hidden by Exam Mode.`;
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
