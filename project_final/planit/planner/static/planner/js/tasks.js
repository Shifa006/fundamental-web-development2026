document.addEventListener(
    "DOMContentLoaded",
    () => {
        initTasksPage();
    }
);


let tasks = [];
let selectedArea = "all";
let selectedView = "all";
let searchQuery = "";


async function initTasksPage() {
    initAreaButtons();
    initViewButtons();
    initSearch();

    document.addEventListener(
        "planit:exam-mode-change",
        async () => {
            if (
                selectedView === "week"
            ) {
                await loadWeek();
            } else {
                renderFilteredTasks();
            }
        }
    );

    await loadTasks();
}


async function loadTasks() {
    showTasksLoading();

    try {
        const data =
            await PlanitAPI.get(
                "/api/tasks/"
            );

        tasks = data.tasks;

        renderFilteredTasks();

        showAllTasks();
    } catch (error) {
        showTasksError(
            error.message
        );
    }
}


async function loadWeek() {
    showTasksLoading();

    const examMode =
        window.PlanitUI.getExamMode()
            ? "1"
            : "0";

    const params =
        new URLSearchParams({
            area: selectedArea,
            exam_mode: examMode,
        });

    try {
        const data =
            await window.PlanitAPI.get(
                `/api/week/?${params}`
            );

        renderWeek(
            data.days
        );

        hideTasksLoading();

        document.querySelector(
            "#allTasksView"
        ).hidden = true;

        document.querySelector(
            "#weekTasksView"
        ).hidden = false;

    } catch (error) {
        showTasksError(
            error.message
        );
    }
}


function initAreaButtons() {
    document
        .querySelectorAll(
            ".filter-button[data-area]"
        )
        .forEach((button) => {
            button.addEventListener(
                "click",
                async () => {
                    document
                        .querySelectorAll(
                            ".filter-button[data-area]"
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

                    if (
                        selectedView ===
                        "week"
                    ) {
                        await loadWeek();
                    } else {
                        renderFilteredTasks();
                    }
                }
            );
        });
}


function initViewButtons() {
    document
        .querySelectorAll(
            ".view-tab[data-view]"
        )
        .forEach((button) => {
            button.addEventListener(
                "click",
                async () => {
                    document
                        .querySelectorAll(
                            ".view-tab[data-view]"
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

                    selectedView =
                        button.dataset.view;

                    if (
                        selectedView ===
                        "week"
                    ) {
                        await loadWeek();
                    } else {
                        renderFilteredTasks();
                        showAllTasks();
                    }
                }
            );
        });
}


function initSearch() {
    const input =
        document.querySelector(
            "#taskSearch"
        );

    if (!input) {
        return;
    }

    input.addEventListener(
        "input",
        () => {
            searchQuery =
                input.value
                    .trim()
                    .toLowerCase();

            if (
                selectedView === "all"
            ) {
                renderFilteredTasks();
            }
        }
    );
}


function getFilteredTasks() {
    const examMode =
        PlanitUI.getExamMode();

    return tasks
        .filter((task) => {
            return (
                selectedArea === "all"
                || task.area
                    === selectedArea
            );
        })
        .filter((task) => {
            return (
                !examMode
                || task.status
                    === "past_exam"
                || task.exam_mode_visible
            );
        })
        .filter((task) => {
            return (
                !searchQuery
                || task.title
                    .toLowerCase()
                    .includes(
                        searchQuery
                    )
            );
        })
        .sort(
            (a, b) =>
                a.attention_rank
                - b.attention_rank
        );
}


function renderFilteredTasks() {
    const list =
        document.querySelector(
            "#archiveTaskList"
        );

    if (!list) {
        return;
    }

    list.replaceChildren();

    const filtered =
        getFilteredTasks();
    
    renderActiveCount(
        filtered
);

    setText(
        "#taskListCount",
        `${filtered.length} ${
            filtered.length === 1
                ? "ITEM"
                : "ITEMS"
        }`
    );

    if (!filtered.length) {
        const message =
            document.createElement(
                "p"
            );

        message.className =
            "empty-message";

        message.textContent =
            "No tasks match these filters.";

        list.append(message);

        return;
    }


    const fragment =
        document.createDocumentFragment();

    filtered.forEach((task) => {
        fragment.append(
            createArchiveTask(
                task
            )
        );
    });

    list.append(fragment);
}


function createArchiveTask(task) {
    const article =
        document.createElement(
            "article"
        );

    article.className =
        "archive-task";


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


    const body =
        document.createElement(
            "div"
        );


    const title =
        document.createElement(
            "strong"
        );

    title.textContent =
        task.title;


    const detail =
        document.createElement(
            "span"
        );

    detail.textContent =
        getTaskDetail(task);


    body.append(
        title,
        detail
    );


    const status =
        document.createElement(
            "span"
        );

    status.className =
        `task-status ${getStatusClass(
            task
        )}`;

    status.textContent =
        getStatusLabel(task);


    article.append(
        check,
        body,
        status
    );

    return article;
}


function renderWeek(days) {
    const grid =
        document.querySelector(
            "#weekGrid"
        );

    if (!grid) {
        return;
    }

    grid.replaceChildren();


    days.forEach((day) => {
        const column =
            document.createElement(
                "article"
            );

        column.className =
            "week-column";


        const header =
            document.createElement(
                "header"
            );


        const name =
            document.createElement(
                "span"
            );

        name.textContent =
            day.weekday
                .slice(0, 3)
                .toUpperCase();


        const number =
            document.createElement(
                "strong"
            );

        number.textContent =
            day.date.slice(-2);


        header.append(
            name,
            number
        );

        column.append(header);


        if (!day.tasks.length) {
            const empty =
                document.createElement(
                    "p"
                );

            empty.className =
                "empty-day";

            empty.textContent =
                "No tasks";

            column.append(empty);
        }


        day.tasks.forEach(
            (task) => {
                const card =
                    document.createElement(
                        "div"
                    );

                card.className =
                    `week-task ${
                        getKindClass(
                            task.kind
                        )
                    }`;

                if (
                    task.status ===
                    "past_exam"
                ) {
                    card.classList.add(
                        "is-past"
                    );
                }


                const title =
                    document.createElement(
                        "strong"
                    );

                title.textContent =
                    task.title;


                const detail =
                    document.createElement(
                        "span"
                    );

                detail.textContent =
                    getTaskDetail(task);


                card.append(
                    title,
                    detail
                );

                column.append(card);
            }
        );


        grid.append(column);
    });
}


function renderActiveCount(filteredTasks) {
    const count =
        filteredTasks.filter(
            (task) =>
                !task.completed
                && task.status
                    !== "past_exam"
        ).length;

    setText(
        "#activeTaskCount",
        String(count)
            .padStart(2, "0")
    );
}


function getTaskDetail(task) {
    if (task.subject) {
        return task.subject.name;
    }

    if (task.project) {
        return task.project.title;
    }

    return capitalize(
        task.area
    );
}


function getStatusLabel(task) {
    if (task.completed) {
        return "Completed";
    }

    if (
        task.status ===
        "past_exam"
    ) {
        return "Past exam";
    }

    if (
        task.status ===
        "overdue"
    ) {
        return task.days_overdue === 1
            ? "1 day late"
            : `${task.days_overdue} days late`;
    }

    if (
        task.status ===
        "no_date"
    ) {
        return "No date";
    }

    return capitalize(
        task.priority
    );
}


function getStatusClass(task) {
    if (
        task.status === "overdue"
    ) {
        return "pastel-peach";
    }

    if (
        task.kind === "exam"
    ) {
        return "pastel-butter";
    }

    if (
        task.kind === "study"
    ) {
        return "pastel-sage";
    }

    if (
        task.area === "personal"
    ) {
        return "pastel-lavender";
    }

    return "pastel-blue";
}


function getKindClass(kind) {
    const classes = {
        assignment:
            "pastel-peach",

        exam:
            "pastel-butter",

        study:
            "pastel-sage",

        general:
            "pastel-lavender",
    };

    return (
        classes[kind]
        || "pastel-blue"
    );
}


function capitalize(value) {
    return (
        value.charAt(0)
            .toUpperCase()
        + value.slice(1)
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


function showTasksLoading() {
    document.querySelector(
        "#tasksLoading"
    ).hidden = false;

    document.querySelector(
        "#tasksError"
    ).hidden = true;

    document.querySelector(
        "#allTasksView"
    ).hidden = true;

    document.querySelector(
        "#weekTasksView"
    ).hidden = true;
}


function hideTasksLoading() {
    document.querySelector(
        "#tasksLoading"
    ).hidden = true;
}


function showAllTasks() {
    hideTasksLoading();

    const error =
        document.querySelector(
            "#tasksError"
        );

    const allView =
        document.querySelector(
            "#allTasksView"
        );

    const weekView =
        document.querySelector(
            "#weekTasksView"
        );

    error.hidden = true;
    allView.hidden = false;
    weekView.hidden = true;
}

function showTasksError(message) {
    hideTasksLoading();

    const error =
        document.querySelector(
            "#tasksError"
        );

    error.textContent =
        message;

    error.hidden =
        false;
}