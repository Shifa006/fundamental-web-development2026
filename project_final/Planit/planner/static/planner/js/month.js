/* Month view (read-only calendar). Dates come from the server (meta.today). */
(function () {
    let viewYear = null;
    let viewMonth = null;
    let data = null;
    let selectedDate = null;
    let options = null;

    const DOT_LABELS = {
        exam: "exam",
        overdue: "overdue",
        academic: "academic",
        personal: "personal",
        completed: "done",
    };

    function monthLabel(year, month) {
        return new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" })
            .format(new Date(year, month - 1, 1));
    }

    function dayLabel(iso) {
        const [year, month, day] = iso.split("-").map(Number);
        return new Intl.DateTimeFormat("en-US", { weekday: "long", day: "numeric", month: "long" })
            .format(new Date(year, month - 1, day));
    }

    async function load(opts) {
        options = opts;
        options.onLoading();

        const params = new URLSearchParams({
            area: options.area,
            exam_mode: options.examMode ? "1" : "0",
        });
        if (viewYear !== null) {
            params.set("year", viewYear);
            params.set("month", viewMonth);
        }

        try {
            data = await window.PlanitAPI.get(`/api/month/?${params}`);
            viewYear = data.year;
            viewMonth = data.month;

            const keep = selectedDate && data.days.some((d) => d.date === selectedDate);
            if (!keep) {
                const today = data.meta.today;
                selectedDate = data.days.some((d) => d.date === today) ? today : data.days[0].date;
            }

            options.onReady();
            document.querySelector("#tasksError").hidden = true;
            document.querySelector("#allTasksView").hidden = true;
            document.querySelector("#weekTasksView").hidden = true;
            document.querySelector("#monthTasksView").hidden = false;
            render();
        } catch (error) {
            options.onError(error.message);
        }
    }

    function visibleTasks(day) {
        return day.tasks.filter(options.matches).sort(options.sorter);
    }

    function render() {
        if (!data) {
            return;
        }

        document.querySelector("#monthTitle").textContent = monthLabel(data.year, data.month);

        const note = document.querySelector("#monthOverdueNote");
        if (data.overdue_before_month > 0) {
            note.textContent = `${data.overdue_before_month} overdue task${data.overdue_before_month === 1 ? "" : "s"} from earlier months — see All tasks.`;
            note.hidden = false;
        } else {
            note.hidden = true;
        }

        const grid = document.querySelector("#monthGrid");
        grid.replaceChildren();

        for (let i = 0; i < data.first_weekday; i += 1) {
            const filler = document.createElement("span");
            filler.className = "month-cell is-empty";
            filler.setAttribute("aria-hidden", "true");
            grid.append(filler);
        }

        data.days.forEach((day) => {
            const shown = visibleTasks(day);
            const cell = document.createElement("button");
            cell.type = "button";
            cell.className = "month-cell";
            if (day.date === data.meta.today) {
                cell.classList.add("is-today");
            }
            if (day.date === selectedDate) {
                cell.classList.add("is-selected");
                cell.setAttribute("aria-pressed", "true");
            } else {
                cell.setAttribute("aria-pressed", "false");
            }

            const number = document.createElement("strong");
            number.textContent = String(Number(day.date.slice(-2)));

            const dots = document.createElement("span");
            dots.className = "month-dots";
            const kinds = [];
            shown.forEach((task) => {
                const kind = task.status === "completed" ? "completed"
                    : task.kind === "exam" ? "exam"
                    : task.status === "overdue" ? "overdue"
                    : task.area;
                if (!kinds.includes(kind)) {
                    kinds.push(kind);
                }
            });
            ["exam", "overdue", "academic", "personal", "completed"]
                .filter((kind) => kinds.includes(kind))
                .slice(0, 3)
                .forEach((kind) => {
                    const dot = document.createElement("i");
                    dot.className = `dot dot-${kind}`;
                    dots.append(dot);
                });

            cell.append(number, dots);

            if (shown.length > 3) {
                const more = document.createElement("small");
                more.textContent = `+${shown.length - 3}`;
                cell.append(more);
            }

            const summary = shown.length
                ? `${shown.length} task${shown.length === 1 ? "" : "s"}: ${kinds.map((k) => DOT_LABELS[k]).join(", ")}`
                : "no tasks";
            cell.setAttribute("aria-label", `${dayLabel(day.date)}, ${summary}`);

            cell.addEventListener("click", () => {
                selectedDate = day.date;
                render();
            });
            grid.append(cell);
        });

        renderDay();
    }

    function renderDay() {
        const day = data.days.find((d) => d.date === selectedDate);
        const list = document.querySelector("#monthDayList");
        list.replaceChildren();
        document.querySelector("#monthDayTitle").textContent = dayLabel(selectedDate);

        const shown = visibleTasks(day);
        if (!shown.length) {
            list.append(window.PlanitUtils.emptyMessage("No tasks on this day."));
        } else {
            shown.forEach((task) => list.append(options.makeRow(task)));
        }

        const add = document.createElement("button");
        add.type = "button";
        add.className = "soft-button month-add";
        add.textContent = "+ Add a task on this day";
        add.addEventListener("click", () => window.PlanitTasks.openCreate({ dueDate: selectedDate }));
        list.append(add);
    }

    function shift(delta) {
        let month = viewMonth + delta;
        let year = viewYear;
        if (month < 1) {
            month = 12;
            year -= 1;
        } else if (month > 12) {
            month = 1;
            year += 1;
        }
        viewYear = year;
        viewMonth = month;
        selectedDate = null;
        load(options);
    }

    function goToday() {
        viewYear = null;
        viewMonth = null;
        selectedDate = null;
        load(options);
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelector("#monthPrev")?.addEventListener("click", () => shift(-1));
        document.querySelector("#monthNext")?.addEventListener("click", () => shift(1));
        document.querySelector("#monthToday")?.addEventListener("click", goToday);
    });

    window.PlanitMonth = { load, rerender: render };
})();
