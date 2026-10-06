document.addEventListener("DOMContentLoaded", () => {
    const password = document.querySelector("#loginPassword");
    const toggle = document.querySelector("#passwordToggle");

    if (!password || !toggle) {
        return;
    }

    toggle.addEventListener("click", () => {
        const reveal = password.type === "password";
        password.type = reveal ? "text" : "password";
        toggle.textContent = reveal ? "Hide" : "Show";
        toggle.setAttribute("aria-pressed", String(reveal));
        password.focus();
    });
});
