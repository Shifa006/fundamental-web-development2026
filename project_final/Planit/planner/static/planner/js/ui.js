document.addEventListener("DOMContentLoaded", () => {
    initExamModeControls();
});


function getExamMode() {
    return localStorage.getItem("planit_exam_mode") === "1";
}


function setExamMode(enabled) {
    localStorage.setItem("planit_exam_mode", enabled ? "1" : "0");
}


function updateExamModeControls() {
    const enabled = getExamMode();

    document.querySelectorAll("[data-exam-toggle]").forEach((control) => {
        control.classList.toggle("is-active", enabled);
        control.setAttribute("aria-pressed", String(enabled));

        const status = control.querySelector(".mode-toggle-status");
        if (status) {
            status.textContent = enabled ? "On" : "Off";
        }
    });

    document.body.classList.toggle("exam-mode-on", enabled);
}


function toggleExamMode() {
    const enabled = !getExamMode();
    setExamMode(enabled);
    updateExamModeControls();

    document.dispatchEvent(
        new CustomEvent("planit:exam-mode-change", {
            detail: { enabled },
        }),
    );
}


function initExamModeControls() {
    const controls = document.querySelectorAll("[data-exam-toggle]");
    if (!controls.length) {
        return;
    }

    updateExamModeControls();

    controls.forEach((control) => {
        control.addEventListener("click", toggleExamMode);
    });
}


window.PlanitUI = {
    getExamMode,
    setExamMode,
    updateExamModeControls,
};
