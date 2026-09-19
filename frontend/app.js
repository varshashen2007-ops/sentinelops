const state = {
    incidents: [],
    selectedIncident: null,
    timeline: [],
    evidence: [],
    recommendations: [],
    loading: false,
    error: null,
};


function setLoading(loading) {
    state.loading = loading;

    const detail = document.getElementById("incident-detail");

    if (loading) {
        detail.innerHTML =
            '<p class="empty-state">Loading incident...</p>';
    }
}


function setError(error) {
    state.error = error;

    const detail = document.getElementById("incident-detail");

    detail.innerHTML = `
        <p class="empty-state">
            ${error}
        </p>
    `;
}


function renderSummary() {
    document.getElementById("incident-count").textContent =
        state.incidents.length;

    document.getElementById("active-count").textContent =
        state.incidents.filter(
            (incident) => incident.status === "active"
        ).length;

    document.getElementById("recommendation-count").textContent =
        state.recommendations.length;
}


function renderIncidents() {
    const container = document.getElementById("incidents");

    if (state.incidents.length === 0) {
        container.innerHTML =
            '<p class="empty-state">No incidents loaded.</p>';
        return;
    }

    container.innerHTML = state.incidents
        .map(
            (incident) => `
                <div
                    class="incident"
                    data-incident-id="${incident.incident_id}"
                >
                    <strong>${incident.incident_id}</strong>
                    <div>Status: ${incident.status}</div>
                    <div>
                        Severity:
                        ${incident.severity ?? "unknown"}
                    </div>
                </div>
            `
        )
        .join("");

    document.querySelectorAll(".incident").forEach((element) => {
        element.addEventListener("click", () => {
            selectIncident(element.dataset.incidentId);
        });
    });
}


function renderIncidentDetail() {
    const container = document.getElementById("incident-detail");

    if (!state.selectedIncident) {
        container.innerHTML =
            '<p class="empty-state">' +
            "Select an incident to view details." +
            "</p>";
        return;
    }

    const incident = state.selectedIncident;

    container.innerHTML = `
        <h3>${incident.incident_id}</h3>

        <p>Status: ${incident.status}</p>

        <p>
            Severity:
            ${incident.severity ?? "unknown"}
        </p>

        <p>
            Evidence items:
            ${state.evidence.length}
        </p>
    `;
}


function renderTimeline() {
    const container = document.getElementById("timeline");

    if (state.timeline.length === 0) {
        container.innerHTML =
            '<p class="empty-state">' +
            "No timeline events loaded." +
            "</p>";
        return;
    }

    container.innerHTML = state.timeline
        .map(
            (event) => `
                <div class="timeline-event">
                    <strong>${event.event_type}</strong>
                    <div>${event.timestamp}</div>
                    <div>Source: ${event.source}</div>
                    ${
                        event.resource
                            ? `<div>Resource: ${event.resource}</div>`
                            : ""
                    }
                </div>
            `
        )
        .join("");
}


function renderRecommendations() {
    const container = document.getElementById("recommendations");

    if (state.recommendations.length === 0) {
        container.innerHTML =
            '<p class="empty-state">' +
            "No recommendations loaded." +
            "</p>";
        return;
    }

    container.innerHTML = state.recommendations
        .map(
            (recommendation) => `
                <div class="recommendation">
                    <strong>${recommendation.action}</strong>

                    ${
                        recommendation.target
                            ? `<div>
                                Target:
                                ${recommendation.target}
                            </div>`
                            : ""
                    }
                </div>
            `
        )
        .join("");
}


function getRemediationAction() {
    const actionType =
        document.getElementById("remediation-action").value;

    const namespace =
        document.getElementById("remediation-namespace").value.trim();

    const resourceName =
        document.getElementById("remediation-resource").value.trim();

    return {
        action_type: actionType,
        resource_type: "deployment",
        namespace: namespace,
        resource_name: resourceName,
        parameters: {},
    };
}


function showRemediationResult(message) {
    document.getElementById("remediation-result").textContent = message;
}


async function runDryRun() {
    try {
        const action = getRemediationAction();

        const result = await dryRunRemediation(action);

        showRemediationResult(result.message);
    } catch (error) {
        showRemediationResult(
            error.message || "Dry run failed."
        );
    }
}


async function executeAction() {
    try {
        const action = getRemediationAction();

        const result = await executeRemediation(action);

        showRemediationResult(result.message);
    } catch (error) {
        showRemediationResult(
            error.message || "Remediation failed."
        );
    }
}


async function selectIncident(incidentId) {
    try {
        setLoading(true);

        const [
            incident,
            timeline,
            evidence,
            recommendations,
        ] = await Promise.all([
            getIncident(incidentId),
            getTimeline(incidentId),
            getEvidence(incidentId),
            getRecommendations(incidentId),
        ]);

        state.selectedIncident = incident;
        state.timeline = timeline;
        state.evidence = evidence;
        state.recommendations = recommendations;
        state.error = null;

        renderSummary();
        renderIncidentDetail();
        renderTimeline();
        renderRecommendations();
    } catch (error) {
        setError(
            error.message || "Unable to load incident data."
        );
    } finally {
        state.loading = false;
    }
}


function render() {
    renderSummary();
    renderIncidents();
    renderIncidentDetail();
    renderTimeline();
    renderRecommendations();
}


document
    .getElementById("dry-run-button")
    ?.addEventListener("click", runDryRun);

document
    .getElementById("execute-button")
    ?.addEventListener("click", executeAction);


render();