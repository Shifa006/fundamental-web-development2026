function parseLocalDate(value) {
    if (!value) {
        return null;
    }

    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
}


function formatDate(value, options = {}) {
    const date = typeof value === "string" ? parseLocalDate(value) : value;

    if (!date) {
        return "No date";
    }

    return new Intl.DateTimeFormat(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric",
            ...options,
        },
    ).format(date);
}


function capitalize(value) {
    if (!value) {
        return "";
    }
    return value.charAt(0).toUpperCase() + value.slice(1);
}


function formatKind(kind) {
    return String(kind)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}


function formatCount(value) {
    return String(value).padStart(2, "0");
}


function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) {
        element.textContent = value;
    }
}


function taskContext(task) {
    if (task.subject) {
        return task.subject.code
            ? `${task.subject.code} · ${task.subject.name}`
            : task.subject.name;
    }

    if (task.project) {
        return task.project.title;
    }

    return capitalize(task.area);
}


function taskStatusLabel(task) {
    if (task.completed) {
        return "Completed";
    }

    if (task.status === "past_exam") {
        return "Past exam";
    }

    if (task.status === "overdue") {
        return task.days_overdue === 1
            ? "1 day late"
            : `${task.days_overdue} days late`;
    }

    if (task.status === "no_date") {
        return "No date";
    }

    return capitalize(task.priority);
}


function kindClass(kind) {
    return {
        assignment: "pastel-peach",
        exam: "pastel-butter",
        study: "pastel-sage",
        general: "pastel-lavender",
    }[kind] || "pastel-blue";
}


function statusClass(task) {
    // The pill text is either a state (late / past exam / completed) or the
    // priority, so colour follows that same meaning, never the task type.
    if (task.completed) {
        return "pastel-blue";
    }
    if (task.status === "overdue") {
        return "pastel-peach";
    }
    if (task.status === "past_exam" || task.status === "no_date") {
        return "pastel-muted";
    }
    if (task.priority === "urgent") {
        return "pastel-peach";
    }
    if (task.priority === "later") {
        return "pastel-muted";
    }
    return "pastel-blue";
}


function showToast(message, tone = "default") {
    const region = document.querySelector("#toastRegion");
    if (!region) {
        return;
    }

    const toast = document.createElement("div");
    toast.className = `planit-toast ${tone === "error" ? "is-error" : ""}`;
    toast.textContent = message;
    region.append(toast);

    window.setTimeout(() => {
        toast.classList.add("is-leaving");
        window.setTimeout(() => toast.remove(), 250);
    }, 2400);
}


function emptyMessage(text) {
    const message = document.createElement("p");
    message.className = "empty-message";
    message.textContent = text;
    return message;
}


window.PlanitUtils = {
    parseLocalDate,
    formatDate,
    capitalize,
    formatKind,
    formatCount,
    setText,
    taskContext,
    taskStatusLabel,
    kindClass,
    statusClass,
    showToast,
    emptyMessage,
};
