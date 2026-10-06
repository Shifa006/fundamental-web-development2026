/* ============================================================================
    Shifa Mama - Creative CV
    script.js

    File map
        1. Configuration and DOM references
        2. Small helpers (safe storage, debounce)
        3. Navigation (burger menu)
        4. Smooth scrolling and active section
        5. Carousel
        6. Contact form (validate, sanitize, store)
        7. Visitor counter
        8. Start-up

    The whole file sits inside an IIFE, so none of these names leak into the
    global scope and collide with another script on the page.
============================================================================ */

(function () {
    "use strict";

    /* ========================================================================
    1. CONFIGURATION AND DOM REFERENCES
    ======================================================================== */

    // Named constants instead of unexplained numbers scattered through the code
    const CONFIG = {
        MOBILE_NAV_OFFSET: 92,      // space kept below the floating bar on phones (px)
        DESKTOP_NAV_GAP: 34,        // extra space added to the bar height on wide screens (px)
        NAV_SCROLLED_AT: 40,        // scroll past this and the bar changes background
        GO_TOP_VISIBLE_AT: 500,     // scroll past this and the go-to-top button appears
        TOP_ZONE: 180,              // inside this distance the page still counts as "top"
        SCROLL_MIN_MS: 420,         // shortest smooth-scroll animation
        SCROLL_MAX_MS: 900,         // longest smooth-scroll animation
        RESIZE_DEBOUNCE_MS: 150,    // wait this long before reacting to a resize
        MIN_MESSAGE_LENGTH: 5       // matches the minlength attribute in the HTML
    };

    // --- Navigation ---
    const navbar = document.getElementById("siteNav");
    const menuButton = document.getElementById("menuButton");
    const navLinks = document.getElementById("navLinks");
    const logoSlot = document.querySelector(".logo-slot");
    const navItems = Array.from(document.querySelectorAll(".nav-link"));
    const goToTop = document.getElementById("goToTop");

    /* Every in-page link except the skip link. The skip link has to keep its
       native behaviour, because that is what moves keyboard focus to <main>. */
    const internalLinks = Array.from(
        document.querySelectorAll('a[href^="#"]:not(.skip-link)')
    );

    // --- Carousel ---
    const projectsSection = document.getElementById("projects");
    const carouselTrack = document.getElementById("carouselTrack");
    const prevButton = document.getElementById("prevSlide");
    const nextButton = document.getElementById("nextSlide");
    const slideCounter = document.getElementById("slideCounter");

    // --- Contact form (queried once, then reused everywhere) ---
    const contactForm = document.getElementById("contactForm");
    const formStatus = document.getElementById("formStatus");
    const nameField = document.getElementById("visitorName");
    const emailField = document.getElementById("visitorEmail");
    const messageField = document.getElementById("visitorMessage");
    const nameError = document.getElementById("nameError");
    const emailError = document.getElementById("emailError");
    const messageError = document.getElementById("messageError");

    // --- Footer ---
    const visitCount = document.getElementById("visitCount");

    // --- Media queries, read as live objects rather than one-off measurements ---
    const mobileQuery = window.matchMedia("(max-width: 760px)");
    const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    /* Form values kept in JavaScript variables, as the workshop brief asks.
        The three separate variables are the required part; contactData groups
        them into one object so they can be turned into JSON in a single step. */
    let visitorName = "";
    let visitorEmail = "";
    let visitorMessage = "";
    let contactData = null;

    // Internal state for the page-scrolling animation
    let navigationLocked = false;   // true while a scroll animation is running
    let scrollAnimationFrame = null;

    /* ========================================================================
    2. SMALL HELPERS
    ======================================================================== */

    /* Safari in private mode throws as soon as storage is touched. Without the
       try/catch the whole script would stop at that line. */
    const safeStorage = {
        get(storage, key) {
            try {
                return storage.getItem(key);
            } catch (error) {
                console.warn("Storage read blocked:", error);
                return null;
            }
        },

        set(storage, key, value) {
            try {
                storage.setItem(key, value);
                return true;
            } catch (error) {
                console.warn("Storage write blocked:", error);
                return false;
            }
        }
    };

    // Delays a call until the events stop arriving. Used for resize.
    function debounce(callback, delay) {
        let timerId = null;

        return function (...args) {
            window.clearTimeout(timerId);
            timerId = window.setTimeout(() => callback.apply(this, args), delay);
        };
    }

    // Turns 3 into "03" for the slide counter
    function padNumber(value) {
        return String(value).padStart(2, "0");
    }

    /* ========================================================================
    3. NAVIGATION (BURGER MENU)
    ======================================================================== */

    function setNavigationExpanded(expanded) {
        navbar.classList.toggle("nav-collapsed", !expanded);

        // Locks the page behind the panel while the mobile menu is open
        document.body.classList.toggle("menu-open", expanded && mobileQuery.matches);

        // inert removes hidden elements from both tab order and pointer events
        navLinks.inert = !expanded;
        logoSlot.inert = !expanded;

        menuButton.setAttribute("aria-expanded", String(expanded));
        menuButton.setAttribute(
            "aria-label",
            expanded ? "Collapse navigation" : "Expand navigation"
        );
    }

    function toggleNavigation() {
        setNavigationExpanded(navbar.classList.contains("nav-collapsed"));
    }

    function initNavigation() {
        // Start collapsed, matching the class already on the markup
        setNavigationExpanded(false);

        menuButton.addEventListener("click", toggleNavigation);

        // Tapping a link on a phone closes the panel
        navItems.forEach((link) => {
            link.addEventListener("click", () => {
                if (mobileQuery.matches) {
                    setNavigationExpanded(false);
                }
            });
        });

        // Clicking anywhere outside the open panel closes it
        document.addEventListener("click", (event) => {
            const menuIsOpen = !navbar.classList.contains("nav-collapsed");

            if (mobileQuery.matches && menuIsOpen && !navbar.contains(event.target)) {
                setNavigationExpanded(false);
            }
        });

        // Escape closes the menu at any screen width
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !navbar.classList.contains("nav-collapsed")) {
                setNavigationExpanded(false);
                menuButton.focus();
            }
        });

        /* Crossing the mobile breakpoint - by rotating the phone or dragging the
        window edge - swaps one navigation layout for the other. Collapsing here
        clears body.menu-open as well, so the page can never be left locked
        with the scroll turned off on a screen that has no panel. */
        mobileQuery.addEventListener("change", () => {
            setNavigationExpanded(false);
        });
    }

    /* ========================================================================
    4. SMOOTH SCROLLING AND ACTIVE SECTION
    ======================================================================== */

    /* The section list is read from the data-section attributes in the HTML,
    so adding a menu item never means editing two places. map() and filter()
    are higher-order array methods. */
    const sectionIds = navItems
        .map((link) => link.dataset.section)
        .filter((id) => id && id !== "top");

    function setActiveNav(sectionId) {
        navItems.forEach((link) => {
            const isActive = link.dataset.section === sectionId;

            link.classList.toggle("active", isActive);

            /* The class only changes the colour. aria-current is what tells a
               screen reader which menu item is the current one. */
            if (isActive) {
                link.setAttribute("aria-current", "true");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    }

    // Works out where to stop, leaving room for the navigation bar
    function getTargetPosition(targetId) {
        if (targetId === "top") {
            return 0;
        }

        const target = document.getElementById(targetId);

        if (!target) {
            return window.scrollY;
        }

        /* Stopping at the section label rather than the section box itself
           keeps the visible heading clear of the bar. */
        const visualAnchor =
            target.querySelector(".section-label") ||
            target.querySelector(".projects-header") ||
            target;

        const navbarOffset = mobileQuery.matches
            ? CONFIG.MOBILE_NAV_OFFSET
            : navbar.offsetHeight + CONFIG.DESKTOP_NAV_GAP;

        return Math.max(
            0,
            visualAnchor.getBoundingClientRect().top + window.scrollY - navbarOffset
        );
    }

    // Easing curve: slow start, quick middle, gentle stop
    function easeInOutCubic(progress) {
        return progress < 0.5
            ? 4 * progress * progress * progress
            : 1 - Math.pow(-2 * progress + 2, 3) / 2;
    }

    function navigateTo(targetId) {
        // Cancel an animation that is still running from a previous click
        if (scrollAnimationFrame) {
            cancelAnimationFrame(scrollAnimationFrame);
            scrollAnimationFrame = null;
        }

        navigationLocked = true;
        setActiveNav(targetId);

        /* Keep the address bar in step with the section, the way a plain anchor
           would. replaceState avoids filling the history with one entry per click. */
        const newHash = targetId === "top"
            ? window.location.pathname + window.location.search
            : `#${targetId}`;
        window.history.replaceState(null, "", newHash);

        const startPosition = window.scrollY;
        const targetPosition = getTargetPosition(targetId);

        // Someone who asked for less motion gets an instant jump instead
        if (reducedMotionQuery.matches) {
            window.scrollTo(0, targetPosition);
            navigationLocked = false;
            return;
        }

        const distance = targetPosition - startPosition;
        const duration = Math.min(
            CONFIG.SCROLL_MAX_MS,
            Math.max(CONFIG.SCROLL_MIN_MS, Math.abs(distance) * 0.42)
        );
        const startTime = performance.now();

        function animateScroll(currentTime) {
            const progress = Math.min((currentTime - startTime) / duration, 1);

            window.scrollTo(0, startPosition + distance * easeInOutCubic(progress));

            if (progress < 1) {
                scrollAnimationFrame = requestAnimationFrame(animateScroll);
                return;
            }

            window.scrollTo(0, targetPosition);
            scrollAnimationFrame = null;
            navigationLocked = false;
            setActiveNav(targetId);
        }

        scrollAnimationFrame = requestAnimationFrame(animateScroll);
    }

    function updateNavbarAppearance() {
        navbar.classList.toggle("scrolled", window.scrollY > CONFIG.NAV_SCROLLED_AT);
        goToTop.classList.toggle("visible", window.scrollY > CONFIG.GO_TOP_VISIBLE_AT);
    }

    // Finds the section currently in view and highlights its menu item
    function updateActiveSection() {
        // While an animated scroll runs, the destination is already highlighted
        if (navigationLocked) {
            return;
        }

        const marker = window.scrollY + navbar.offsetHeight + window.innerHeight * 0.3;
        let activeSection = "top";

        sectionIds.forEach((sectionId) => {
            const section = document.getElementById(sectionId);

            if (section && section.offsetTop <= marker) {
                activeSection = sectionId;
            }
        });

        if (window.scrollY < CONFIG.TOP_ZONE) {
            activeSection = "top";
        }

        setActiveNav(activeSection);
    }

    function initScrollBehaviour() {
        internalLinks.forEach((link) => {
            link.addEventListener("click", (event) => {
                const href = link.getAttribute("href");

                if (!href || href === "#") {
                    return;
                }

                const targetId = href.slice(1);

                if (targetId === "top" || document.getElementById(targetId)) {
                    event.preventDefault();
                    navigateTo(targetId);
                }
            });
        });

        let scrollFrameRequested = false;

        /* passive: true promises the browser this listener never calls
        preventDefault(), which keeps scrolling smooth on phones.
        requestAnimationFrame limits the work to one run per frame. */
        window.addEventListener("scroll", () => {
            if (scrollFrameRequested) {
                return;
            }

            scrollFrameRequested = true;

            window.requestAnimationFrame(() => {
                updateNavbarAppearance();
                updateActiveSection();
                scrollFrameRequested = false;
            });
        }, { passive: true });

        // Debounced, because the mobile address bar fires resize constantly
        window.addEventListener("resize", debounce(() => {
            if (mobileQuery.matches) {
                setNavigationExpanded(false);
            }

            updateActiveSection();
        }, CONFIG.RESIZE_DEBOUNCE_MS));

        goToTop.addEventListener("click", () => navigateTo("top"));

        updateNavbarAppearance();
        updateActiveSection();
    }

    /* ========================================================================
    5. CAROUSEL
    The slider is written as one object that owns its own state and methods.
    Inside those methods, `this` refers to the carousel object itself.
    ======================================================================== */

    const carousel = {
        // State
        index: 0,
        slides: Array.from(carouselTrack.children),

        // Moves the strip and keeps counter and accessibility state in step
        render() {
            carouselTrack.style.transform = `translateX(-${this.index * 100}%)`;

            slideCounter.textContent =
                `${padNumber(this.index + 1)} / ${padNumber(this.slides.length)}`;

            /* Off-screen slides stay in the DOM, so they have to be hidden from
               the tab order and from screen readers on purpose. */
            this.slides.forEach((slide, position) => {
                const isActive = position === this.index;

                slide.inert = !isActive;
                slide.setAttribute("aria-hidden", String(!isActive));
            });
        },

        // The modulo keeps the index inside the list and wraps it around
        next() {
            this.index = (this.index + 1) % this.slides.length;
            this.render();
        },

        previous() {
            this.index = (this.index - 1 + this.slides.length) % this.slides.length;
            this.render();
        },

        init() {
            nextButton.addEventListener("click", () => this.next());
            prevButton.addEventListener("click", () => this.previous());

            /* Listening on the whole section catches key presses from the
            focusable carousel window and from the two buttons alike,
            because those events bubble up to here. */
            projectsSection.addEventListener("keydown", (event) => {
                if (event.key === "ArrowRight") {
                    event.preventDefault();
                    this.next();
                }

                if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    this.previous();
                }
            });

            this.render();
        }
    };

    /* ========================================================================
    6. CONTACT FORM
    ======================================================================== */

    /* Strips tags, control characters and repeated whitespace out of the input.
    This is basic cleaning, not full XSS protection. The real safety comes
    from writing user text with textContent instead of innerHTML. */
    function sanitizeInput(value) {
        return value
            .replace(/<[^>]*>/g, "")
            .replace(/[<>]/g, "")
            .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "")
            .replace(/[ \t]+/g, " ")
            .replace(/\n{3,}/g, "\n\n")
            .trim();
    }

    // Shows or clears the error state of one field. Returns true when valid.
    function setFieldState(field, errorElement, message) {
        const hasError = Boolean(message);

        field.classList.toggle("invalid", hasError);
        errorElement.textContent = message;

        // aria-invalid tells screen readers as well, not just the red underline
        if (hasError) {
            field.setAttribute("aria-invalid", "true");
        } else {
            field.removeAttribute("aria-invalid");
        }

        return !hasError;
    }

    /* Turns the reason reported by the Constraint Validation API into a
       message that says what to do, instead of one generic sentence. */
    function describeValidity(field, label) {
        if (field.validity.valueMissing) {
            return `Please enter your ${label}.`;
        }

        if (field.validity.typeMismatch || field.validity.patternMismatch) {
            return field.title || `Please enter a valid ${label}.`;
        }

        return "";
    }

    /* Checks every field and hands back the cleaned message alongside the
       result, so sanitizeInput does not have to run twice on submit. */
    function validateFormFields() {
        const cleanMessage = sanitizeInput(messageField.value);

        let messageProblem = "";

        if (!cleanMessage) {
            messageProblem = "Please enter a message.";
        } else if (cleanMessage.length < CONFIG.MIN_MESSAGE_LENGTH) {
            messageProblem =
                `Your message must contain at least ${CONFIG.MIN_MESSAGE_LENGTH} characters.`;
        }

        const nameValid = setFieldState(
            nameField, nameError, describeValidity(nameField, "name")
        );
        const emailValid = setFieldState(
            emailField, emailError, describeValidity(emailField, "email address")
        );
        const messageValid = setFieldState(messageField, messageError, messageProblem);

        return {
            isValid: nameValid && emailValid && messageValid,
            cleanMessage
        };
    }

    function clearFormErrors() {
        [nameField, emailField, messageField].forEach((field) => {
            field.classList.remove("invalid");
            field.removeAttribute("aria-invalid");
        });

        [nameError, emailError, messageError].forEach((errorElement) => {
            errorElement.textContent = "";
        });
    }

    function handleSubmit(event) {
        // The form is handled entirely in JavaScript, so stop the page reload
        event.preventDefault();

        const result = validateFormFields();

        if (!result.isValid) {
            formStatus.textContent = "Please correct the highlighted fields.";

            // Optional chaining, in case no field carries the class
            contactForm.querySelector(".invalid")?.focus();
            return;
        }

        // Store the cleaned values in the variables the brief asks for
        visitorName = sanitizeInput(nameField.value);
        visitorEmail = sanitizeInput(emailField.value);
        visitorMessage = result.cleanMessage;

        // Group them into one object, ready to be turned into JSON
        contactData = {
            name: visitorName,
            email: visitorEmail,
            message: visitorMessage,
            submittedAt: new Date().toISOString()
        };

        // Exposed so the object can be inspected from the console during a demo
        window.contactData = contactData;

        /* Object -> JSON string, because storage can only hold text.
        The write can be refused (Safari private mode, storage full), so the
        message below reports what actually happened rather than assuming. */
        const wasSaved = safeStorage.set(
            sessionStorage, "contactData", JSON.stringify(contactData)
        );

        // textContent is safer than innerHTML: it never runs the text as markup
        formStatus.textContent = wasSaved
            ? `Thank you, ${visitorName}. Your message is saved in this browser for this session.`
            : `Thank you, ${visitorName}. This browser blocked storage, so the message was kept in memory only.`;

        contactForm.reset();
        clearFormErrors();
    }

    // Reads a message saved earlier: JSON string -> object
    function restoreSavedMessage() {
        const raw = safeStorage.get(sessionStorage, "contactData");

        if (!raw) {
            return;
        }

        try {
            const saved = JSON.parse(raw);
            const savedTime = new Date(saved.submittedAt).toLocaleTimeString();

            formStatus.textContent = `A message from ${saved.name} was saved at ${savedTime}.`;
        } catch (error) {
            console.warn("Saved contact data could not be read:", error);
        }
    }

    function initContactForm() {
        contactForm.addEventListener("submit", handleSubmit);

        // Clear the error as soon as the visitor starts fixing that field
        const fieldPairs = [
            [nameField, nameError],
            [emailField, emailError],
            [messageField, messageError]
        ];

        fieldPairs.forEach(([field, errorElement]) => {
            field.addEventListener("input", () => {
                if (field.classList.contains("invalid")) {
                    setFieldState(field, errorElement, "");
                }
            });
        });

        restoreSavedMessage();
    }

    /* ========================================================================
    7. VISITOR COUNTER
    localStorage lives in one browser on one device, so this number is a
    local visit count, not the number of people who have seen the site.
    A real site-wide total needs a server or an analytics service.
    ======================================================================== */

    function initVisitorCounter() {
        let totalVisits = Number(safeStorage.get(localStorage, "visitCount")) || 0;

        // Count once per browser session rather than once per page refresh
        if (!safeStorage.get(sessionStorage, "visitCounted")) {
            totalVisits += 1;
            safeStorage.set(localStorage, "visitCount", String(totalVisits));
            safeStorage.set(sessionStorage, "visitCounted", "true");
        }

        visitCount.textContent = String(totalVisits);
    }

    /* ========================================================================
    8. START-UP
    The script tag uses defer, so the DOM is ready by the time this runs.
    ======================================================================== */

    initNavigation();
    initScrollBehaviour();
    carousel.init();
    initContactForm();
    initVisitorCounter();
})();
