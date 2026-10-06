document.addEventListener("DOMContentLoaded", () => {
    initTaskView();
    initTaskSearch();
    initTaskFilters();
    initCheckboxes();
});


function initTaskView() {
    const tabs = document.querySelectorAll("[data-view]");

    if (!tabs.length) {
        return;
    }

    const allView = document.querySelector("#allTasksView");
    const weekView = document.querySelector("#weekTasksView");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((item) => {
                item.classList.remove("is-active");
            });

            tab.classList.add("is-active");

            const view = tab.dataset.view;

            allView?.classList.toggle(
                "is-visible",
                view === "all"
            );

            weekView?.classList.toggle(
                "is-visible",
                view === "week"
            );
        });
    });
}


function initTaskSearch() {
    const search = document.querySelector("#taskSearch");

    if (!search) {
        return;
    }

    search.addEventListener("input", () => {
        const query = search.value
            .trim()
            .toLowerCase();

        document
            .querySelectorAll(".archive-task")
            .forEach((task) => {
                const title =
                    task.dataset.title || "";

                task.hidden =
                    !title.includes(query);
            });
    });
}


function initTaskFilters() {
    const buttons =
        document.querySelectorAll("[data-filter]");

    if (!buttons.length) {
        return;
    }

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            buttons.forEach((item) => {
                item.classList.remove("is-active");
            });

            button.classList.add("is-active");

            const filter =
                button.dataset.filter;

            document
                .querySelectorAll(".archive-task")
                .forEach((task) => {
                    task.hidden =
                        filter !== "all" &&
                        task.dataset.area !== filter;
                });
        });
    });
}


function initCheckboxes() {
    document
        .querySelectorAll(".check-box")
        .forEach((button) => {
            button.addEventListener("click", () => {
                button.classList.toggle("is-checked");
            });
        });
}