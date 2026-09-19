const demoIncidents = {
    "INC-2407": {
        title: "API latency spike",
        severity: "CRITICAL",
        service: "api-gateway",
        namespace: "production",
        description:
            "Elevated p95 latency detected on production API workloads.",
    },

    "INC-2406": {
        title: "Memory pressure",
        severity: "WARNING",
        service: "worker-pool",
        namespace: "production",
        description:
            "Memory utilization above threshold on worker nodes.",
    },

    "INC-2405": {
        title: "Pod restart detected",
        severity: "MINOR",
        service: "payments",
        namespace: "production",
        description:
            "Payment service restarted after a failed health check.",
    },
};

const demoTimeline = {
    "INC-2407": [
        {
            timestamp: "08:42",
            source: "Prometheus",
            event:
                "API latency anomaly detected",
        },
        {
            timestamp: "08:45",
            source: "Loki",
            event:
                "Increased 5xx responses observed",
        },
        {
            timestamp: "08:47",
            source: "Prometheus",
            event:
                "Database connection saturation detected",
        },
        {
            timestamp: "08:50",
            source: "Correlation",
            event:
                "Incident escalated to CRITICAL",
        },
    ],
};

const demoEvidence = {
    "INC-2407": [
        {
            source: "Prometheus",
            type: "metric",
            description:
                "API p95 latency increased to 1.8 seconds.",
        },
        {
            source: "Loki",
            type: "log",
            description:
                "Elevated upstream timeout errors observed.",
        },
    ],
};

const demoDiagnosis = {
    "INC-2407": {
        diagnosis:
            "Upstream database connection saturation",
        confidence: 0.948,
    },
};

const demoRecommendations = {
    "INC-2407": [
        {
            action:
                "Scale API deployment",
            target:
                "deployment/api-gateway",
        },
    ],
};

let selectedIncidentId = "INC-2407";

const incidentRows =
    document.querySelectorAll(".incident-row");

const sidebar =
    document.getElementById("sidebar");

const mobileOverlay =
    document.getElementById("mobileOverlay");

const openSidebarButton =
    document.getElementById("openSidebar");

const closeSidebarButton =
    document.getElementById("closeSidebar");

const currentTime =
    document.getElementById("currentTime");

const currentDate =
    document.getElementById("currentDate");

const remediationResult =
    document.getElementById("remediationResult");

const actionType =
    document.getElementById("actionType");

const replicaCount =
    document.getElementById("replicaCount");


function updateClock() {
    const now = new Date();

    currentTime.textContent =
        now.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });

    currentDate.textContent =
        now.toLocaleDateString([], {
            weekday: "long",
            month: "short",
            day: "numeric",
            year: "numeric",
        });
}


function setSidebar(open) {
    sidebar.classList.toggle(
        "open",
        open
    );

    mobileOverlay.classList.toggle(
        "visible",
        open
    );
}


async function getIncident(incidentId) {
    try {
        return await window.getIncident(
            incidentId
        );
    } catch (error) {
        return (
            demoIncidents[incidentId] ||
            null
        );
    }
}


async function getTimeline(incidentId) {
    try {
        return await window.getTimeline(
            incidentId
        );
    } catch (error) {
        return (
            demoTimeline[incidentId] ||
            []
        );
    }
}


async function getEvidence(incidentId) {
    try {
        return await window.getEvidence(
            incidentId
        );
    } catch (error) {
        return (
            demoEvidence[incidentId] ||
            []
        );
    }
}


async function getDiagnosis(incidentId) {
    try {
        return await window.getDiagnosis(
            incidentId
        );
    } catch (error) {
        return (
            demoDiagnosis[incidentId] ||
            null
        );
    }
}


async function getRecommendations(
    incidentId
) {
    try {
        return await window.getRecommendations(
            incidentId
        );
    } catch (error) {
        return (
            demoRecommendations[incidentId] ||
            []
        );
    }
}


function getRemediationAction() {
    const action =
        actionType.value;

    const parameters = {};

    if (action === "scale") {
        parameters.replicas =
            Number(
                replicaCount.value
            );
    }

    return {
        action_type: action,
        resource_type: "deployment",
        namespace: "production",
        resource_name: "api-gateway",
        parameters,
    };
}


function renderTimeline(events) {
    const timeline =
        document.querySelector(
            ".timeline"
        );

    if (!timeline || !events?.length) {
        return;
    }

    timeline.innerHTML =
        events
            .map(
                (event, index) => {
                    const timestamp =
                        event.timestamp ||
                        "--:--";

                    const source =
                        event.source ||
                        "Telemetry";

                    const description =
                        event.event ||
                        event.description ||
                        event.data?.message ||
                        "Telemetry event detected.";

                    const critical =
                        index ===
                        events.length - 1;

                    return `
                        <div class="timeline-item">
                            <div class="timeline-marker ${
                                critical
                                    ? "critical"
                                    : ""
                            }"></div>

                            <div class="timeline-time">
                                ${timestamp}
                                <small>UTC</small>
                            </div>

                            <div class="timeline-event">
                                <strong>
                                    ${description}
                                </strong>

                                <span>
                                    Correlated infrastructure signal.
                                </span>
                            </div>

                            <span class="source-tag">
                                ${source}
                            </span>
                        </div>
                    `;
                }
            )
            .join("");
}


function renderEvidence(evidence) {
    if (!evidence?.length) {
        return;
    }

    const evidenceCount =
        document.querySelector(
            ".panel-kicker"
        );

    /*
     * Evidence is already represented in the
     * incident detail/timeline UI. Keep the
     * loaded evidence available for future
     * detailed evidence panels.
     */
    window.currentIncidentEvidence =
        evidence;

    if (evidenceCount) {
        evidenceCount.dataset.evidenceCount =
            String(evidence.length);
    }
}


function renderDiagnosis(diagnosis) {
    if (!diagnosis) {
        return;
    }

    const diagnosisTitle =
        document.querySelector(
            ".diagnosis-box strong"
        );

    if (diagnosisTitle) {
        diagnosisTitle.textContent =
            diagnosis.diagnosis ||
            "Correlated infrastructure diagnosis";
    }
}


function renderRecommendations(
    recommendations
) {
    if (!recommendations?.length) {
        return;
    }

    const recommendationTitle =
        document.querySelector(
            ".recommendation-content strong"
        );

    if (recommendationTitle) {
        recommendationTitle.textContent =
            recommendations[0].action ||
            "Review recommended remediation";
    }
}


async function selectIncident(id) {
    selectedIncidentId = id;

    incidentRows.forEach((row) => {
        row.classList.toggle(
            "selected",
            row.dataset.incidentId === id
        );
    });

    const [
        incident,
        timeline,
        evidence,
        diagnosis,
        recommendations,
    ] = await Promise.all([
        getIncident(id),
        getTimeline(id),
        getEvidence(id),
        getDiagnosis(id),
        getRecommendations(id),
    ]);

    if (!incident) {
        return;
    }

    const title =
        document.getElementById(
            "detailTitle"
        );

    const detailId =
        document.querySelector(
            ".detail-id"
        );

    const badge =
        document.querySelector(
            ".detail-header .badge"
        );

    if (title) {
        title.textContent =
            incident.title ||
            demoIncidents[id]?.title ||
            "Incident";
    }

    if (detailId) {
        const namespace =
            incident.namespace ||
            demoIncidents[id]?.namespace ||
            "production";

        const service =
            incident.service ||
            demoIncidents[id]?.service ||
            "unknown";

        detailId.textContent =
            `${id} · ${namespace} · ${service}`;
    }

    if (badge) {
        const severity =
            incident.severity ||
            demoIncidents[id]?.severity ||
            "UNKNOWN";

        badge.textContent =
            severity;

        badge.className =
            "badge " +
            (
                severity === "CRITICAL"
                    ? "critical-badge"
                    : severity === "WARNING"
                        ? "warning-badge"
                        : "minor-badge"
            );
    }

    renderTimeline(
        timeline
    );

    renderEvidence(
        evidence
    );

    renderDiagnosis(
        diagnosis
    );

    renderRecommendations(
        recommendations
    );

    document
        .getElementById(
            "remediationSection"
        )
        ?.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
        });
}


function showResult(
    message,
    success = true
) {
    remediationResult.hidden =
        false;

    remediationResult.textContent =
        message;

    remediationResult.style.color =
        success
            ? "var(--green)"
            : "var(--red)";

    remediationResult.style.borderColor =
        success
            ? "rgba(61,226,155,.14)"
            : "rgba(255,92,122,.14)";

    remediationResult.style.background =
        success
            ? "rgba(61,226,155,.05)"
            : "rgba(255,92,122,.05)";
}


async function runDryRun() {
    const button =
        document.getElementById(
            "dryRunButton"
        );

    button.disabled = true;

    button.textContent =
        "Running dry-run...";

    try {
        const payload =
            getRemediationAction();

        const result =
            await window.dryRunRemediation(
                payload
            );

        showResult(
            result.message ||
                "Dry-run validation completed successfully.",
            result.success !== false
        );
    } catch (error) {
        showResult(
            "Demo mode: remediation passed local validation. Connect SentinelOps API to execute against Kubernetes.",
            true
        );
    } finally {
        button.disabled = false;

        button.innerHTML =
            "<span>◌</span> Run dry-run";
    }
}


async function executeAction() {
    const confirmed =
        window.confirm(
            "Execute this remediation action against the selected deployment?"
        );

    if (!confirmed) {
        return;
    }

    const button =
        document.getElementById(
            "executeButton"
        );

    button.disabled = true;

    button.textContent =
        "Executing...";

    try {
        const payload =
            getRemediationAction();

        const result =
            await window.executeRemediation(
                payload
            );

        showResult(
            result.message ||
                "Remediation request completed.",
            result.success !== false
        );
    } catch (error) {
        showResult(
            "Demo mode: execution is simulated because no SentinelOps API server is connected.",
            true
        );
    } finally {
        button.disabled = false;

        button.innerHTML =
            "<span>⚡</span> Execute remediation";
    }
}


function configureActionControls() {
    const scale =
        actionType.value === "scale";

    replicaCount.disabled =
        !scale;

    replicaCount.style.opacity =
        scale ? "1" : ".45";
}


function setupNavigation() {
    document
        .querySelectorAll(".nav-item")
        .forEach((item) => {
            item.addEventListener(
                "click",
                () => {
                    document
                        .querySelectorAll(
                            ".nav-item"
                        )
                        .forEach((nav) =>
                            nav.classList.remove(
                                "active"
                            )
                        );

                    item.classList.add(
                        "active"
                    );

                    setSidebar(false);
                }
            );
        });
}


function setupIncidentRows() {
    incidentRows.forEach((row) => {
        row.addEventListener(
            "click",
            () => {
                selectIncident(
                    row.dataset
                        .incidentId
                );
            }
        );
    });
}


function setupButtons() {
    openSidebarButton?.addEventListener(
        "click",
        () => setSidebar(true)
    );

    closeSidebarButton?.addEventListener(
        "click",
        () => setSidebar(false)
    );

    mobileOverlay?.addEventListener(
        "click",
        () => setSidebar(false)
    );

    document
        .getElementById(
            "openRemediation"
        )
        ?.addEventListener(
            "click",
            () => {
                document
                    .getElementById(
                        "remediationSection"
                    )
                    ?.scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                    });
            }
        );

    document
        .getElementById(
            "dryRunButton"
        )
        ?.addEventListener(
            "click",
            runDryRun
        );

    document
        .getElementById(
            "executeButton"
        )
        ?.addEventListener(
            "click",
            executeAction
        );

    actionType?.addEventListener(
        "change",
        configureActionControls
    );
}


function setupTouchBehavior() {
    document
        .querySelectorAll(
            "button, select, input"
        )
        .forEach((element) => {
            element.style.touchAction =
                "manipulation";
        });
}


async function initialize() {
    updateClock();

    setInterval(
        updateClock,
        30_000
    );

    setupNavigation();
    setupIncidentRows();
    setupButtons();
    setupTouchBehavior();
    configureActionControls();

    await selectIncident(
        selectedIncidentId
    );
}


initialize();