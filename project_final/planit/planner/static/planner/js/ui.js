document.addEventListener("DOMContentLoaded", () => {
    initExamModeButton();
});


function getExamMode() {
    return localStorage.getItem("planit_exam_mode") === "1";
}


function setExamMode(enabled) {
    localStorage.setItem("planit_exam_mode", enabled ? "1" : "0");
}


function updateExamModeButton(button) {
    const enabled = getExamMode();
    button.classList.toggle("is-active", enabled);
    button.setAttribute("aria-pressed", String(enabled));
    button.textContent = enabled ? "Exam Mode On" : "Exam Mode";
}


function initExamModeButton() {
    const button = document.querySelector("#examModeButton");

    if (!button) {
        return;
    }

    updateExamModeButton(button);

    button.addEventListener("click", () => {
        const enabled = !getExamMode();
        setExamMode(enabled);
        updateExamModeButton(button);

        document.dispatchEvent(
            new CustomEvent("planit:exam-mode-change", {
                detail: { enabled },
            })
        );
    });
}


window.PlanitUI = {
    getExamMode,
    setExamMode,
};
