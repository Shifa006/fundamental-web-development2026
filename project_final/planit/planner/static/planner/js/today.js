document.addEventListener(
    "DOMContentLoaded",
    () => {
        initTodayPage();
    }
);


let selectedArea = "all";


async function initTodayPage() {
    initAreaFilters();

    document.addEventListener(
        "planit:exam-mode-change",
        loadToday
    );

    document.addEventListener(
        "planit:tasks-changed",
        loadToday
    );

    await loadToday();
}


function initAreaFilters() {
    document
        .querySelectorAll(".area-filter")
        .forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    document
                        .querySelectorAll(
                            ".area-filter"
                        )
                        .forEach(
                            (item) => {
                                item.classList.remove(
                                    "is-active"
                                );
                            }
                        );

                    button.classList.add(
                        "is-active"
                    );

                    selectedArea =
                        button.dataset.area;

                    loadToday();
                }
            );
        });
}


async function loadToday() {
    showLoading();

    const examMode =
        PlanitUI.getExamMode()
            ? "1"
            : "0";

    const params =
        new URLSearchParams({
            area: selectedArea,
            exam_mode: examMode,
        });

    try {
        const data =
            await PlanitAPI.get(
                `/api/today/?${params}`
            );

        renderToday(data);
        showContent();
    } catch (error) {
        showError(error.message);
    }
}


function renderToday(data) {
    renderDate(data.meta.today);

    renderProgress(
        data.progress
    );

    renderTaskList(
        "#todayTaskList",
        data.today,
        "Nothing is due today."
    );

    renderTaskList(
        "#overdueTaskList",
        data.overdue,
        "Nothing overdue."
    );

    setText(
        "#todayCount",
        formatCount(
            data.today.length
        )
    );

    setText(
        "#overdueCount",
        formatCount(
            data.overdue.length
        )
    );

    renderNextExam(
        data.next_exam
    );

    renderHiddenCount(
        data.hidden_by_exam_mode
    );
}


function renderDate(isoDate) {
    const date =
        parseLocalDate(
            isoDate
        );

    const longDate =
        new Intl.DateTimeFormat(
            "en-US",
            {
                weekday: "long",
                month: "long",
                day: "numeric",
            }
        ).format(date);

    setText(
        "#todayDate",
        longDate
    );

    setText(
        "#dateMonth",
        new Intl.DateTimeFormat(
            "en-US",
            {
                month: "short",
            }
        )
            .format(date)
            .toUpperCase()
    );

    setText(
        "#dateNumber",
        String(
            date.getDate()
        ).padStart(2, "0")
    );

    setText(
        "#dateWeekday",
        new Intl.DateTimeFormat(
            "en-US",
            {
                weekday: "short",
            }
        )
            .format(date)
            .toUpperCase()
    );

    renderCalendar(date);
}


function renderProgress(progress) {
    setText(
        "#progressCompleted",
        String(
            progress.completed
        ).padStart(2, "0")
    );

    setText(
        "#progressTotal",
        String(
            progress.total
        ).padStart(2, "0")
    );

    const bar =
        document.querySelector(
            "#todayProgressBar"
        );

    if (!bar) {
        return;
    }

    const percent =
        progress.percent ?? 0;

    bar.style.width =
        `${percent}%`;

    setText(
        "#progressText",
        progress.percent === null
            ? "No tasks due today"
            : `${percent}% completed`
    );
}


function renderTaskList(
    selector,
    tasks,
    emptyMessage,
) {
    const container =
        document.querySelector(
            selector
        );

    if (!container) {
        return;
    }

    container.replaceChildren();

    if (!tasks.length) {
        const message =
            document.createElement(
                "p"
            );

        message.className =
            "empty-message";

        message.textContent =
            emptyMessage;

        container.append(
            message
        );

        return;
    }

    const fragment =
        document.createDocumentFragment();

    tasks.forEach((task) => {
        fragment.append(
            createTaskRow(task)
        );
    });

    container.append(
        fragment
    );
}


function createTaskRow(task) {
    const article =
        document.createElement(
            "article"
        );

    article.className =
        "task-row";

    if (task.completed) {
        article.classList.add(
            "is-complete"
        );
    }


    const check =
        document.createElement(
            "button"
        );

    check.type =
        "button";

    check.className =
        "check-box";

    if (task.completed) {
        check.classList.add(
            "is-checked"
        );
    }

    check.setAttribute(
        "aria-label",
        task.completed
            ? `Uncomplete ${task.title}`
            : `Complete ${task.title}`
    );

    check.addEventListener(
        "click",
        async () => {
            check.disabled =
                true;

            try {
                await window.PlanitTasks
                    .toggleCompleted(
                        task
                    );
            } catch (error) {
                check.disabled =
                    false;

                window.alert(
                    error.message
                );
            }
        }
    );

    const copy =
        document.createElement(
            "div"
        );

    copy.className =
        "task-copy";


    const title =
        document.createElement(
            "strong"
        );

    title.textContent =
        task.title;


    const context =
        document.createElement(
            "span"
        );

    context.textContent =
        getTaskContext(task);


    copy.append(
        title,
        context
    );


    const kind =
        document.createElement(
            "span"
        );

    kind.className =
        `category-pill ${getKindClass(
            task.kind
        )}`;

    kind.textContent =
        formatKind(
            task.kind
        );


    const priority =
        document.createElement(
            "span"
        );

    priority.className =
        "priority-text";

    if (
        task.priority === "urgent" ||
        task.status === "overdue"
    ) {
        priority.classList.add(
            "urgent"
        );
    }

    priority.textContent =
        getTaskStatusText(task);


    article.append(
        check,
        copy,
        kind,
        priority
    );

    return article;
}


function getTaskContext(task) {
    if (task.subject) {
        return task.subject.name;
    }

    if (task.project) {
        return task.project.title;
    }

    return task.area === "personal"
        ? "Personal"
        : "Academic";
}


function getTaskStatusText(task) {
    if (task.completed) {
        return "Done";
    }

    if (task.status === "overdue") {
        const days =
            task.days_overdue;

        return days === 1
            ? "1 day late"
            : `${days} days late`;
    }

    return capitalize(
        task.priority
    );
}


function renderNextExam(exam) {
    const countdown =
        document.querySelector(
            "#examCountdown"
        );

    if (!exam) {
        setText(
            "#nextExamTitle",
            "No upcoming exam"
        );

        setText(
            "#nextExamDate",
            "Your schedule is clear."
        );

        if (countdown) {
            countdown.hidden =
                true;
        }

        return;
    }

    setText(
        "#nextExamTitle",
        exam.title
    );

    const date =
        parseLocalDate(
            exam.due_date
        );

    setText(
        "#nextExamDate",
        new Intl.DateTimeFormat(
            "en-US",
            {
                weekday: "long",
                month: "long",
                day: "numeric",
            }
        ).format(date)
    );

    if (countdown) {
        countdown.hidden =
            false;
    }

    setText(
        "#examDays",
        exam.days_left
    );
}


function renderHiddenCount(count) {
    const element =
        document.querySelector(
            "#examHiddenMessage"
        );

    if (!element) {
        return;
    }

    if (!count) {
        element.hidden =
            true;

        return;
    }

    element.textContent =
        `${count} active item${
            count === 1 ? "" : "s"
        } hidden by Exam Mode.`;

    element.hidden =
        false;
}


function renderCalendar(date) {
    setText(
        "#calendarMonth",
        new Intl.DateTimeFormat(
            "en-US",
            {
                month: "long",
            }
        ).format(date)
    );

    setText(
        "#calendarYear",
        date.getFullYear()
    );

    const calendar =
        document.querySelector(
            "#miniCalendar"
        );

    if (!calendar) {
        return;
    }

    calendar.replaceChildren();

    [
        "M",
        "T",
        "W",
        "T",
        "F",
        "S",
        "S",
    ].forEach((name) => {
        const label =
            document.createElement(
                "span"
            );

        label.className =
            "day-name";

        label.textContent =
            name;

        calendar.append(label);
    });


    const year =
        date.getFullYear();

    const month =
        date.getMonth();

    const firstDay =
        new Date(
            year,
            month,
            1
        );

    const lastDay =
        new Date(
            year,
            month + 1,
            0
        );

    const mondayIndex =
        (
            firstDay.getDay()
            + 6
        ) % 7;

    for (
        let i = 0;
        i < mondayIndex;
        i += 1
    ) {
        calendar.append(
            document.createElement(
                "span"
            )
        );
    }


    for (
        let day = 1;
        day <= lastDay.getDate();
        day += 1
    ) {
        const cell =
            document.createElement(
                "span"
            );

        cell.textContent =
            day;

        if (
            day === date.getDate()
        ) {
            cell.classList.add(
                "current-day"
            );
        }

        calendar.append(cell);
    }
}


function parseLocalDate(value) {
    const [
        year,
        month,
        day,
    ] = value
        .split("-")
        .map(Number);

    return new Date(
        year,
        month - 1,
        day
    );
}


function setText(
    selector,
    value,
) {
    const element =
        document.querySelector(
            selector
        );

    if (element) {
        element.textContent =
            value;
    }
}


function formatCount(value) {
    return String(
        value
    ).padStart(2, "0");
}


function formatKind(kind) {
    return kind
        .replace("_", " ")
        .replace(
            /\b\w/g,
            (character) =>
                character.toUpperCase()
        );
}


function capitalize(value) {
    return (
        value.charAt(0)
            .toUpperCase()
        + value.slice(1)
    );
}


function getKindClass(kind) {
    const classes = {
        assignment:
            "pastel-butter",

        study:
            "pastel-sage",

        exam:
            "pastel-peach",

        general:
            "pastel-lavender",
    };

    return (
        classes[kind]
        || "pastel-blue"
    );
}


function showLoading() {
    setVisibility(
        "#todayLoading",
        true
    );

    setVisibility(
        "#todayContent",
        false
    );

    setVisibility(
        "#todayError",
        false
    );
}


function showContent() {
    setVisibility(
        "#todayLoading",
        false
    );

    setVisibility(
        "#todayContent",
        true
    );
}


function showError(message) {
    setVisibility(
        "#todayLoading",
        false
    );

    setVisibility(
        "#todayContent",
        false
    );

    const element =
        document.querySelector(
            "#todayError"
        );

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.hidden =
        false;
}


function setVisibility(
    selector,
    visible,
) {
    const element =
        document.querySelector(
            selector
        );

    if (element) {
        element.hidden =
            !visible;
    }
}