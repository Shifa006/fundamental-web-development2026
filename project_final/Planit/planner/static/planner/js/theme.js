(function () {
    const STORAGE_KEY = "planit_theme";
    const THEMES = new Set(["mint", "night"]);

    function getTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);
        return THEMES.has(saved) ? saved : "mint";
    }

    function applyTheme(theme) {
        const next = THEMES.has(theme) ? theme : "mint";
        document.documentElement.dataset.theme = next;
        document.body?.setAttribute("data-theme", next);

        const themeColor = document.querySelector('meta[name="theme-color"]');
        if (themeColor) {
            themeColor.setAttribute("content", next === "night" ? "#1f2830" : "#d8eee2");
        }

        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            const night = next === "night";
            button.classList.toggle("is-night", night);
            button.setAttribute("aria-pressed", String(night));
            button.setAttribute("title", night ? "Switch to Mint Day" : "Switch to Night Quest");
        });

        return next;
    }

    function setTheme(theme) {
        const next = applyTheme(theme);
        localStorage.setItem(STORAGE_KEY, next);
        document.dispatchEvent(new CustomEvent("planit:theme-change", { detail: { theme: next } }));
    }

    function toggleTheme() {
        setTheme(getTheme() === "night" ? "mint" : "night");
    }

    function initTheme() {
        applyTheme(getTheme());
        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            button.addEventListener("click", toggleTheme);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initTheme);
    } else {
        initTheme();
    }

    window.PlanitTheme = {
        getTheme,
        setTheme,
        toggleTheme,
    };
})();
