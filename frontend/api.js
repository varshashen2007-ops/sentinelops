const API_BASE_URL = "/api";


async function request(path, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${path}`,
        {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            ...options,
        }
    );

    let body;

    try {
        body = await response.json();
    } catch {
        throw new Error(
            `API returned HTTP ${response.status}.`
        );
    }

    if (!response.ok) {
        throw new Error(
            body.message || "API request failed."
        );
    }

    return body;
}


async function getIncident(incidentId) {
    return request(
        `/incidents/${encodeURIComponent(incidentId)}`
    );
}


async function getTimeline(incidentId) {
    return request(
        `/incidents/${encodeURIComponent(incidentId)}/timeline`
    );
}


async function getEvidence(incidentId) {
    return request(
        `/incidents/${encodeURIComponent(incidentId)}/evidence`
    );
}


async function getRecommendations(incidentId) {
    return request(
        `/incidents/${encodeURIComponent(incidentId)}/recommendations`
    );
}


async function dryRunRemediation(action) {
    return request(
        "/remediation/dry-run",
        {
            method: "POST",
            body: JSON.stringify(action),
        }
    );
}


async function executeRemediation(action) {
    return request(
        "/remediation/execute",
        {
            method: "POST",
            body: JSON.stringify(action),
        }
    );
}