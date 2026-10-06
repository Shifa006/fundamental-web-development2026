document.addEventListener(
    "DOMContentLoaded",
    () => {
        initTaskActions();
    }
);


let editingTaskId = null;
let taskOptions = null;


async function initTaskActions() {
    const addButton =
        document.querySelector(
            "#addTaskButton"
        );

    const form =
        document.querySelector(
            "#taskForm"
        );

    const area =
        document.querySelector(
            "#taskArea"
        );

    const project =
        document.querySelector(
            "#taskProject"
        );


    addButton?.addEventListener(
        "click",
        () => {
            openCreateTask();
        }
    );


    form?.addEventListener(
        "submit",
        submitTaskForm
    );


    area?.addEventListener(
        "change",
        updateTaskFormRules
    );


    project?.addEventListener(
        "change",
        syncProjectSubject
    );


    try {
        await loadTaskOptions();
    } catch (error) {
        console.error(
            error
        );
    }
}


async function loadTaskOptions() {
    taskOptions =
        await PlanitAPI.get(
            "/api/task-options/"
        );

    renderTaskOptions();
}


function renderTaskOptions() {
    const subjectSelect =
        document.querySelector(
            "#taskSubject"
        );

    const projectSelect =
        document.querySelector(
            "#taskProject"
        );


    subjectSelect.replaceChildren();

    const noSubject =
        document.createElement(
            "option"
        );

    noSubject.value = "";
    noSubject.textContent =
        "No subject";

    subjectSelect.append(
        noSubject
    );


    taskOptions.subjects
        .forEach((subject) => {
            const option =
                document.createElement(
                    "option"
                );

            option.value =
                subject.id;

            option.textContent =
                subject.code
                    ? `${subject.code} — ${subject.name}`
                    : subject.name;

            subjectSelect.append(
                option
            );
        });


    projectSelect.replaceChildren();

    const noProject =
        document.createElement(
            "option"
        );

    noProject.value = "";
    noProject.textContent =
        "No project";

    projectSelect.append(
        noProject
    );


    taskOptions.projects
        .forEach((project) => {
            const option =
                document.createElement(
                    "option"
                );

            option.value =
                project.id;

            option.textContent =
                project.title;

            option.dataset.subjectId =
                project.subject_id ?? "";

            projectSelect.append(
                option
            );
        });
}


function getDefaultArea() {
    const active =
        document.querySelector(
            "[data-area].is-active"
        );

    if (
        active
        && active.dataset.area
        && active.dataset.area
            !== "all"
    ) {
        return active.dataset.area;
    }

    return "academic";
}


function resetTaskForm() {
    const form =
        document.querySelector(
            "#taskForm"
        );

    form.reset();

    document.querySelector(
        "#taskArea"
    ).value =
        getDefaultArea();

    document.querySelector(
        "#taskKind"
    ).value =
        "general";

    document.querySelector(
        "#taskPriority"
    ).value =
        "normal";

    document.querySelector(
        "#taskFormError"
    ).hidden =
        true;

    document.querySelector(
        "#taskMoreOptions"
    ).open =
        false;

    updateTaskFormRules();
}


function openCreateTask() {
    editingTaskId = null;

    resetTaskForm();

    document.querySelector(
        "#taskModalTitle"
    ).textContent =
        "Add task";

    document.querySelector(
        "#taskSubmitButton"
    ).textContent =
        "Add task";

    showTaskModal();
}


function openEditTask(task) {
    editingTaskId =
        task.id;

    resetTaskForm();


    document.querySelector(
        "#taskModalTitle"
    ).textContent =
        "Edit task";

    document.querySelector(
        "#taskSubmitButton"
    ).textContent =
        "Save changes";


    document.querySelector(
        "#taskTitle"
    ).value =
        task.title;

    document.querySelector(
        "#taskDescription"
    ).value =
        task.description || "";

    document.querySelector(
        "#taskArea"
    ).value =
        task.area;

    document.querySelector(
        "#taskKind"
    ).value =
        task.kind;

    document.querySelector(
        "#taskPriority"
    ).value =
        task.priority;

    document.querySelector(
        "#taskDueDate"
    ).value =
        task.due_date || "";

    document.querySelector(
        "#taskSubject"
    ).value =
        task.subject?.id || "";

    document.querySelector(
        "#taskProject"
    ).value =
        task.project?.id || "";

    document.querySelector(
        "#taskMoreOptions"
    ).open =
        true;

    updateTaskFormRules();

    showTaskModal();
}


function showTaskModal() {
    const modalElement =
        document.querySelector(
            "#taskModal"
        );

    const modal =
        bootstrap.Modal
            .getOrCreateInstance(
                modalElement
            );

    modal.show();

    modalElement.addEventListener(
        "shown.bs.modal",
        () => {
            document.querySelector(
                "#taskTitle"
            ).focus();
        },
        {
            once: true,
        }
    );
}


function hideTaskModal() {
    const modal =
        bootstrap.Modal
            .getInstance(
                document.querySelector(
                    "#taskModal"
                )
            );

    modal?.hide();
}


function updateTaskFormRules() {
    const area =
        document.querySelector(
            "#taskArea"
        ).value;

    const kind =
        document.querySelector(
            "#taskKind"
        );

    const subject =
        document.querySelector(
            "#taskSubject"
        );


    const personal =
        area === "personal";


    Array.from(
        kind.options
    ).forEach((option) => {
        option.disabled =
            personal
            && option.value
                !== "general";
    });


    if (
        personal
        && kind.value
            !== "general"
    ) {
        kind.value =
            "general";
    }


    subject.disabled =
        personal;

    if (personal) {
        subject.value =
            "";
    }


    updateProjectAvailability();
}


function updateProjectAvailability() {
    const personal =
        document.querySelector(
            "#taskArea"
        ).value
        === "personal";

    const project =
        document.querySelector(
            "#taskProject"
        );


    Array.from(
        project.options
    ).forEach((option) => {
        if (!option.value) {
            return;
        }

        const academicProject =
            Boolean(
                option.dataset
                    .subjectId
            );

        option.disabled =
            personal
            && academicProject;
    });


    if (
        project.selectedOptions[0]
            ?.disabled
    ) {
        project.value =
            "";
    }
}


function syncProjectSubject() {
    const project =
        document.querySelector(
            "#taskProject"
        );

    const selected =
        project.selectedOptions[0];

    const subjectId =
        selected?.dataset
            .subjectId;


    if (subjectId) {
        document.querySelector(
            "#taskSubject"
        ).value =
            subjectId;
    }
}


function buildTaskPayload() {
    return {
        title:
            document.querySelector(
                "#taskTitle"
            ).value,

        description:
            document.querySelector(
                "#taskDescription"
            ).value,

        area:
            document.querySelector(
                "#taskArea"
            ).value,

        kind:
            document.querySelector(
                "#taskKind"
            ).value,

        priority:
            document.querySelector(
                "#taskPriority"
            ).value,

        due_date:
            document.querySelector(
                "#taskDueDate"
            ).value || null,

        subject_id:
            document.querySelector(
                "#taskSubject"
            ).value || null,

        project_id:
            document.querySelector(
                "#taskProject"
            ).value || null,
    };
}


async function submitTaskForm(event) {
    event.preventDefault();

    const errorBox =
        document.querySelector(
            "#taskFormError"
        );

    const submit =
        document.querySelector(
            "#taskSubmitButton"
        );


    errorBox.hidden =
        true;

    submit.disabled =
        true;


    try {
        const payload =
            buildTaskPayload();


        if (editingTaskId) {
            await PlanitAPI.patch(
                `/api/tasks/${editingTaskId}/`,
                payload
            );
        } else {
            await PlanitAPI.post(
                "/api/tasks/",
                payload
            );
        }


        hideTaskModal();

        notifyTasksChanged();

    } catch (error) {
        errorBox.textContent =
            error.message;

        errorBox.hidden =
            false;

    } finally {
        submit.disabled =
            false;
    }
}


async function toggleCompleted(
    task,
) {
    await PlanitAPI.patch(
        `/api/tasks/${task.id}/`,
        {
            completed:
                !task.completed,
        }
    );

    notifyTasksChanged();
}


async function deleteTask(task) {
    const confirmed =
        window.confirm(
            `Delete "${task.title}"?`
        );

    if (!confirmed) {
        return;
    }

    await PlanitAPI.delete(
        `/api/tasks/${task.id}/`
    );

    notifyTasksChanged();
}


function notifyTasksChanged() {
    document.dispatchEvent(
        new CustomEvent(
            "planit:tasks-changed"
        )
    );
}


window.PlanitTasks = {
    openCreate:
        openCreateTask,

    openEdit:
        openEditTask,

    toggleCompleted,

    delete:
        deleteTask,
};