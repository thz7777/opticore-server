"use strict";

(function () {

    const STORAGE_KEY = "optiforge_settings";

    const DEFAULT_SETTINGS = {
        theme: "dark",
        accent: "orange",
        animations: true,
        notifications: true,
        startup: false
    };


    const $ = (selector) => {
        return document.querySelector(selector);
    };


    const $$ = (selector) => {
        return Array.from(
            document.querySelectorAll(selector)
        );
    };


    // =========================================================
    // SETTINGS
    // =========================================================

    function loadSettings() {

        try {

            const saved =
                localStorage.getItem(
                    STORAGE_KEY
                );


            if (!saved) {
                return {
                    ...DEFAULT_SETTINGS
                };
            }


            const parsed =
                JSON.parse(saved);


            if (
                !parsed ||
                typeof parsed !== "object"
            ) {
                return {
                    ...DEFAULT_SETTINGS
                };
            }


            return {
                ...DEFAULT_SETTINGS,
                ...parsed
            };

        } catch (error) {

            console.error(
                "Failed to load settings:",
                error
            );

            return {
                ...DEFAULT_SETTINGS
            };
        }
    }


    let settings =
        loadSettings();


    function saveSettings() {

        try {

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(settings)
            );

        } catch (error) {

            console.error(
                "Failed to save settings:",
                error
            );
        }
    }


    // =========================================================
    // HELPERS
    // =========================================================

    function getTime() {

        return new Date().toLocaleTimeString(
            "ro-RO",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );
    }


    function escapeHtml(value) {

        return String(value)
            .replaceAll(
                "&",
                "&amp;"
            )
            .replaceAll(
                "<",
                "&lt;"
            )
            .replaceAll(
                ">",
                "&gt;"
            )
            .replaceAll(
                '"',
                "&quot;"
            )
            .replaceAll(
                "'",
                "&#039;"
            );
    }


    function addLog(message) {

        const log =
            $("#log");


        if (!log) {

            console.log(
                "[OptiForge]",
                message
            );

            return;
        }


        const line =
            document.createElement(
                "div"
            );

        line.className =
            "log-line";


        const time =
            document.createElement(
                "span"
            );

        time.className =
            "log-time";

        time.textContent =
            getTime();


        const text =
            document.createElement(
                "span"
            );

        text.textContent =
            String(message);


        line.appendChild(time);
        line.appendChild(text);


        log.appendChild(line);


        log.scrollTop =
            log.scrollHeight;
    }


    function setLogStatus(status) {

        const element =
            $("#log-status-text");


        if (element) {
            element.textContent =
                status;
        }
    }


    // =========================================================
    // PYWEBVIEW BRIDGE
    // =========================================================

    function isPythonReady() {

        return (
            typeof window.pywebview !== "undefined" &&
            window.pywebview !== null &&
            window.pywebview.api !== undefined &&
            window.pywebview.api !== null
        );
    }


    function waitForPython(
        timeout = 15000
    ) {

        return new Promise(
            (resolve) => {

                if (isPythonReady()) {

                    resolve(true);

                    return;
                }


                let completed =
                    false;


                const onReady =
                    () => {

                        if (completed) {
                            return;
                        }

                        completed =
                            true;

                        window.removeEventListener(
                            "pywebviewready",
                            onReady
                        );

                        resolve(
                            true
                        );
                    };


                window.addEventListener(
                    "pywebviewready",
                    onReady
                );


                setTimeout(
                    () => {

                        if (completed) {
                            return;
                        }

                        completed =
                            true;

                        window.removeEventListener(
                            "pywebviewready",
                            onReady
                        );

                        resolve(
                            isPythonReady()
                        );

                    },
                    timeout
                );
            }
        );
    }


    async function callPython(
        action,
        ...args
    ) {

        const ready =
            await waitForPython();


        if (!ready) {

            addLog(
                "Python backend is not connected."
            );

            return {
                success: false,
                reason:
                    "Python backend is not connected."
            };
        }


        try {

            const api =
                window.pywebview.api;


            switch (action) {

                case "run_optimization":

                    return await api.run_optimization(
                        args[0]
                    );


                case "optimize_all":

                    return await api.optimize_all();


                case "logout":

                    return await api.logout();


                case "validate_license":

                    return await api.validate_license(
                        args[0]
                    );


                case "restore_license":

                    return await api.restore_license();


                case "get_license_state":

                    return await api.get_license_state();


                case "get_settings":

                    return await api.get_settings();


                case "save_settings":

                    return await api.save_settings(
                        ...args
                    );


                case "set_startup":

                    return await api.set_startup(
                        args[0]
                    );


                case "get_system_info":

                    return await api.get_system_info();


                default:

                    throw new Error(
                        `Unknown Python API action: ${action}`
                    );
            }

        } catch (error) {

            console.error(
                `Python API error (${action}):`,
                error
            );


            addLog(
                `Backend error: ${
                    error?.message ||
                    error
                }`
            );


            return {
                success: false,
                reason:
                    error?.message ||
                    String(error)
            };
        }
    }


    // =========================================================
    // SETTINGS UI
    // =========================================================

    function applySettings() {

        const body =
            document.body;


        if (!body) {
            return;
        }


        body.setAttribute(
            "data-theme",
            settings.theme
        );


        body.setAttribute(
            "data-accent",
            settings.accent
        );


        body.classList.toggle(
            "no-animations",
            !Boolean(
                settings.animations
            )
        );


        const themeSelect =
            $("#theme-select");


        if (themeSelect) {

            themeSelect.value =
                settings.theme;
        }


        const animationsToggle =
            $("#animations-toggle");


        if (animationsToggle) {

            animationsToggle.checked =
                Boolean(
                    settings.animations
                );
        }


        const notificationsToggle =
            $("#notifications-toggle");


        if (notificationsToggle) {

            notificationsToggle.checked =
                Boolean(
                    settings.notifications
                );
        }


        const startupToggle =
            $("#startup-toggle");


        if (startupToggle) {

            startupToggle.checked =
                Boolean(
                    settings.startup
                );
        }
    }


    async function persistSettings() {

        saveSettings();


        try {

            await callPython(
                "save_settings",
                settings.theme,
                settings.accent,
                settings.animations,
                settings.notifications,
                settings.startup
            );

        } catch (error) {

            console.error(
                "Settings backend error:",
                error
            );
        }
    }


    // =========================================================
    // NAVIGATION
    // =========================================================

    const PAGE_NAMES = {

        dashboard: "Dashboard",
        cleaning: "Cleaning",
        network: "Network",
        gaming: "Gaming",
        startup: "Startup",
        performance: "Performance",
        privacy: "Privacy",
        license: "License",
        account: "Account",
        settings: "Settings"

    };


    function openPage(pageName) {

        const target =
            $(`#page-${pageName}`);


        if (!target) {

            console.warn(
                "Page does not exist:",
                pageName
            );

            return;
        }


        $$(".page").forEach(
            (page) => {

                page.classList.remove(
                    "active"
                );
            }
        );


        target.classList.add(
            "active"
        );


        $$(".nav-item").forEach(
            (button) => {

                button.classList.toggle(
                    "active",
                    button.dataset.page === pageName
                );
            }
        );


        const title =
            $("#page-title");


        if (title) {

            title.textContent =
                PAGE_NAMES[pageName] ||
                pageName;
        }


        const content =
            $(".content");


        if (content) {

            content.scrollTop =
                0;
        }


        addLog(
            `Opened ${
                PAGE_NAMES[pageName] ||
                pageName
            }.`
        );
    }


    function initializeNavigation() {

        $$(".nav-item").forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const page =
                            button.dataset.page;


                        if (page) {

                            openPage(
                                page
                            );
                        }
                    }
                );
            }
        );


        const settingsButton =
            $("#settings-button");


        if (settingsButton) {

            settingsButton.addEventListener(
                "click",
                () => {

                    openPage(
                        "settings"
                    );
                }
            );
        }


        const backDashboard =
            $("#back-dashboard");


        if (backDashboard) {

            backDashboard.addEventListener(
                "click",
                () => {

                    openPage(
                        "dashboard"
                    );
                }
            );
        }
    }


    // =========================================================
    // THEME
    // =========================================================

    function initializeTheme() {

        const select =
            $("#theme-select");


        if (!select) {
            return;
        }


        select.addEventListener(
            "change",
            async () => {

                const theme =
                    select.value;


                if (
                    theme !== "dark" &&
                    theme !== "light"
                ) {
                    return;
                }


                settings.theme =
                    theme;


                applySettings();


                await persistSettings();


                addLog(
                    `Theme changed to ${theme}.`
                );
            }
        );
    }


    // =========================================================
    // ANIMATIONS
    // =========================================================

    function initializeAnimations() {

        const toggle =
            $("#animations-toggle");


        if (!toggle) {
            return;
        }


        toggle.addEventListener(
            "change",
            async () => {

                settings.animations =
                    toggle.checked;


                applySettings();


                await persistSettings();


                addLog(
                    settings.animations
                        ? "Animations enabled."
                        : "Animations disabled."
                );
            }
        );
    }


    // =========================================================
    // NOTIFICATIONS
    // =========================================================

    function initializeNotifications() {

        const toggle =
            $("#notifications-toggle");


        if (!toggle) {
            return;
        }


        toggle.addEventListener(
            "change",
            async () => {

                settings.notifications =
                    toggle.checked;


                await persistSettings();


                addLog(
                    settings.notifications
                        ? "Notifications enabled."
                        : "Notifications disabled."
                );
            }
        );
    }


    // =========================================================
    // STARTUP
    // =========================================================

    function initializeStartup() {

        const toggle =
            $("#startup-toggle");


        if (!toggle) {
            return;
        }


        toggle.addEventListener(
            "change",
            async () => {

                const enabled =
                    toggle.checked;


                addLog(
                    enabled
                        ? "Enabling Start with Windows..."
                        : "Disabling Start with Windows..."
                );


                const result =
                    await callPython(
                        "set_startup",
                        enabled
                    );


                if (
                    !result ||
                    !result.success
                ) {

                    addLog(
                        `Startup error: ${
                            result?.reason ||
                            "Unknown error."
                        }`
                    );


                    settings.startup =
                        !enabled;


                    applySettings();


                    return;
                }


                settings.startup =
                    enabled;


                await persistSettings();


                addLog(
                    enabled
                        ? "Start with Windows enabled."
                        : "Start with Windows disabled."
                );
            }
        );
    }


    // =========================================================
    // RESET SETTINGS
    // =========================================================

    function initializeReset() {

        const button =
            $("#reset-settings");


        if (!button) {
            return;
        }


        button.addEventListener(
            "click",
            async () => {

                settings = {
                    ...DEFAULT_SETTINGS
                };


                applySettings();


                await persistSettings();


                addLog(
                    "Settings restored to default."
                );
            }
        );
    }


    // =========================================================
    // LICENSE UI
    // =========================================================

    function updateLicenseUI(
        state
    ) {

        const active =
            Boolean(
                state &&
                state.active
            );


        const tier =
            state?.tier_label ||
            state?.tier ||
            "";


        const tierText =
            tier
                ? tier.toUpperCase()
                : "NONE";


        const profilePlan =
            $(".profile-plan");


        if (profilePlan) {

            profilePlan.textContent =
                active
                    ? `${tierText} LICENSE`
                    : "NO LICENSE";
        }


        const licenseBadge =
            $("#license-badge") ||
            $(".license-badge");


        if (licenseBadge) {

            licenseBadge.innerHTML =
                `
                <span class="status-dot"></span>
                ${escapeHtml(
                    active
                        ? tierText
                        : "UNLICENSED"
                )}
                `;
        }


        const licenseTier =
            $("#license-tier") ||
            $(".license-tier");


        if (licenseTier) {

            licenseTier.textContent =
                tierText;
        }


        const licenseActive =
            $("#license-active") ||
            $(".license-active");


        if (licenseActive) {

            licenseActive.innerHTML =
                `
                <span class="status-dot"></span>
                ${active ? "ACTIVE" : "INACTIVE"}
                `;
        }


        const dashboardLicense =
            $("#dashboard-license-status");


        if (dashboardLicense) {

            dashboardLicense.textContent =
                active
                    ? tierText
                    : "NONE";
        }
    }


    function setLicenseMessage(
        message,
        success = false
    ) {

        const element =
            $("#license-message");


        if (!element) {
            return;
        }


        element.textContent =
            String(message);


        element.style.color =
            success
                ? "#22c55e"
                : "#ef4444";
    }


    // =========================================================
    // LICENSE ACTIVATION
    // =========================================================

    function initializeLicense() {

        const activateButton =
            $("#activate-license-button");


        const input =
            $("#license-key-input");


        const refreshButton =
            $("#refresh-license-button");


        if (!activateButton || !input) {
            return;
        }


        activateButton.addEventListener(
            "click",
            async () => {

                const key =
                    input.value
                        .trim()
                        .toUpperCase();


                if (!key) {

                    setLicenseMessage(
                        "Introdu o cheie de licenta."
                    );

                    return;
                }


                activateButton.disabled =
                    true;


                setLicenseMessage(
                    "Se verifica licenta...",
                    false
                );


                setLogStatus(
                    "VERIFYING"
                );


                try {

                    const result =
                        await callPython(
                            "validate_license",
                            key
                        );


                    if (
                        result &&
                        result.success
                    ) {

                        input.value =
                            "";


                        const state = {

                            active: true,

                            license_status:
                                "active",

                            tier:
                                result.tier,

                            tier_label:
                                result.tier_label,

                            expires_at:
                                result.expires_at,

                            optimizations:
                                result.optimizations ||
                                []

                        };


                        updateLicenseUI(
                            state
                        );


                        setLicenseMessage(
                            `Licenta ${
                                result.tier_label ||
                                result.tier ||
                                ""
                            } a fost activata cu succes.`,
                            true
                        );


                        addLog(
                            `License activated: ${
                                result.tier_label ||
                                result.tier ||
                                "Unknown"
                            }`
                        );


                    } else {

                        updateLicenseUI({
                            active: false,
                            license_status: "invalid",
                            tier: "",
                            tier_label: "",
                            expires_at: null
                        });


                        setLicenseMessage(
                            result?.reason ||
                            "Licenta invalida."
                        );


                        addLog(
                            `License activation failed: ${
                                result?.reason ||
                                "Unknown error."
                            }`
                        );
                    }


                } catch (error) {

                    console.error(
                        "License activation error:",
                        error
                    );


                    setLicenseMessage(
                        error?.message ||
                        String(error)
                    );

                } finally {

                    activateButton.disabled =
                        false;


                    setLogStatus(
                        "READY"
                    );
                }
            }
        );


        input.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter"
                ) {

                    event.preventDefault();

                    activateButton.click();
                }
            }
        );


        if (refreshButton) {

            refreshButton.addEventListener(
                "click",
                async () => {

                    refreshButton.disabled =
                        true;


                    setLicenseMessage(
                        "Se verifica licenta salvata...",
                        false
                    );


                    setLogStatus(
                        "VERIFYING"
                    );


                    try {

                        const result =
                            await callPython(
                                "restore_license"
                            );


                        if (
                            result &&
                            result.success
                        ) {

                            updateLicenseUI({
                                active: true,
                                license_status:
                                    "active",
                                tier:
                                    result.tier,
                                tier_label:
                                    result.tier_label,
                                expires_at:
                                    result.expires_at,
                                optimizations:
                                    result.optimizations ||
                                    []
                            });


                            setLicenseMessage(
                                `Licenta ${
                                    result.tier_label ||
                                    result.tier ||
                                    ""
                                } este activa.`,
                                true
                            );


                            addLog(
                                "Saved license restored."
                            );


                        } else {

                            updateLicenseUI({
                                active: false,
                                license_status:
                                    "unlicensed",
                                tier: "",
                                tier_label: "",
                                expires_at: null
                            });


                            setLicenseMessage(
                                result?.reason ||
                                "Nu exista o licenta valida salvata."
                            );
                        }


                    } catch (error) {

                        console.error(
                            "License refresh error:",
                            error
                        );


                        setLicenseMessage(
                            error?.message ||
                            String(error)
                        );

                    } finally {

                        refreshButton.disabled =
                            false;


                        setLogStatus(
                            "READY"
                        );
                    }
                }
            );
        }
    }


    // =========================================================
    // OPTIMIZATION
    // =========================================================

    const ACTION_NAMES = {

        cleaning:
            "System cleaning",

        network:
            "Network optimization",

        gaming:
            "Gaming optimization",

        startup:
            "Startup optimization",

        performance:
            "Performance optimization",

        temp_cleaner:
            "Temporary files cleaning",

        network_boost:
            "Network optimization",

        startup_optimizer:
            "Startup optimization",

        performance_mode:
            "Performance mode",

        game_mode:
            "Game mode",

        ssd_trim:
            "SSD / TRIM maintenance",

        system_cleanup:
            "System cleanup",

        visual_optimizer:
            "Visual optimization",

        system_repair:
            "Windows integrity check"
    };


    async function runAction(
        action,
        button
    ) {

        if (!action) {
            return;
        }


        const readable =
            ACTION_NAMES[action] ||
            action;


        if (button) {

            button.disabled =
                true;
        }


        addLog(
            `${readable} started.`
        );


        setLogStatus(
            "WORKING"
        );


        try {

            const result =
                await callPython(
                    "run_optimization",
                    action
                );


            if (
                result &&
                result.success
            ) {

                addLog(
                    `${readable} completed.`
                );

            } else {

                addLog(
                    `${readable} failed: ${
                        result?.reason ||
                        "Unknown backend error."
                    }`
                );
            }


            return result;

        } catch (error) {

            console.error(
                "Optimization error:",
                error
            );


            addLog(
                `${readable} failed: ${
                    error?.message ||
                    error
                }`
            );


        } finally {

            if (button) {

                button.disabled =
                    false;
            }


            setLogStatus(
                "READY"
            );
        }
    }


    function initializeActionButtons() {

        $$("[data-action]").forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    async () => {

                        const action =
                            button.dataset.action;


                        if (!action) {
                            return;
                        }


                        await runAction(
                            action,
                            button
                        );
                    }
                );
            }
        );
    }


    // =========================================================
    // OPTIMIZE ALL
    // =========================================================

    function initializeOptimizeAll() {

        const button =
            $("#optimize-all");


        if (!button) {
            return;
        }


        button.addEventListener(
            "click",
            async () => {

                if (button.disabled) {
                    return;
                }


                button.disabled =
                    true;


                setLogStatus(
                    "OPTIMIZING"
                );


                addLog(
                    "Starting full optimization..."
                );


                try {

                    const result =
                        await callPython(
                            "optimize_all"
                        );


                    if (
                        result &&
                        result.success
                    ) {

                        addLog(
                            `Full optimization finished: ${
                                result.completed
                            }/${
                                result.total
                            } modules completed.`
                        );

                    } else {

                        addLog(
                            `Full optimization failed: ${
                                result?.reason ||
                                "Unknown error."
                            }`
                        );
                    }


                } catch (error) {

                    console.error(
                        "Optimize all error:",
                        error
                    );


                    addLog(
                        `Full optimization failed: ${
                            error?.message ||
                            error
                        }`
                    );


                } finally {

                    button.disabled =
                        false;


                    setLogStatus(
                        "READY"
                    );
                }
            }
        );
    }


    // =========================================================
    // LOGOUT
    // =========================================================

    function initializeLogout() {

        const button =
            $("#logout-button");


        if (!button) {
            return;
        }


        button.addEventListener(
            "click",
            async () => {

                if (button.disabled) {
                    return;
                }


                button.disabled =
                    true;


                addLog(
                    "Logging out..."
                );


                try {

                    const result =
                        await callPython(
                            "logout"
                        );


                    if (
                        result &&
                        result.success
                    ) {

                        updateLicenseUI({
                            active: false,
                            license_status:
                                "unlicensed",
                            tier: "",
                            tier_label: "",
                            expires_at: null,
                            optimizations: []
                        });


                        setLicenseMessage(
                            "Licenta a fost dezactivata."
                        );


                        addLog(
                            "Logged out successfully."
                        );


                        openPage(
                            "dashboard"
                        );


                    } else {

                        addLog(
                            `Logout failed: ${
                                result?.reason ||
                                "Unknown error."
                            }`
                        );
                    }


                } catch (error) {

                    console.error(
                        "Logout error:",
                        error
                    );


                    addLog(
                        `Logout failed: ${
                            error?.message ||
                            error
                        }`
                    );


                } finally {

                    button.disabled =
                        false;
                }
            }
        );
    }


    // =========================================================
    // PYTHON LOG
    // =========================================================

    window.receiveLog =
        function (message) {

            addLog(
                message
            );
        };


    // =========================================================
    // PYWEBVIEW READY
    // =========================================================

    async function handlePythonReady() {

        addLog(
            "Python backend connected."
        );


        setLogStatus(
            "READY"
        );


        try {

            const state =
                await callPython(
                    "get_license_state"
                );


            if (state) {

                updateLicenseUI(
                    state
                );
            }


        } catch (error) {

            console.error(
                "License state error:",
                error
            );
        }


        try {

            const backendSettings =
                await callPython(
                    "get_settings"
                );


            if (
                backendSettings &&
                backendSettings.success
            ) {

                settings = {
                    ...settings,
                    ...backendSettings
                };


                delete settings.success;


                saveSettings();


                applySettings();
            }


        } catch (error) {

            console.error(
                "Settings load error:",
                error
            );
        }
    }


    window.addEventListener(
        "pywebviewready",
        handlePythonReady
    );


    // =========================================================
    // INITIALIZATION
    // =========================================================

    function initialize() {

        applySettings();


        initializeNavigation();

        initializeTheme();

        initializeAnimations();

        initializeNotifications();

        initializeStartup();

        initializeReset();

        initializeLicense();

        initializeActionButtons();

        initializeOptimizeAll();

        initializeLogout();


        openPage(
            "dashboard"
        );


        addLog(
            "OptiForge frontend loaded."
        );


        if (
            isPythonReady()
        ) {

            handlePythonReady();

        } else {

            setLogStatus(
                "WAITING"
            );
        }
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            {
                once: true
            }
        );

    } else {

        initialize();
    }

})();
