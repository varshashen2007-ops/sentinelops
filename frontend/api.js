const API_BASE_URL =
    window.SENTINELOPS_API_BASE_URL || "";


async function apiRequest(
    path,
    options = {}
) {
    const response =
        await fetch(
            `${API_BASE_URL}${path}`,
            {
                headers: {
                    "Content-Type":
                        "application/json",
                    ...(options.headers || {}),
                },
                ...options,
            }
        );

    const contentType =
        response.headers.get(
            "content-type"
        ) || "";

    const body =
        contentType.includes(
            "application/json"
        )
            ? await response.json()
            : await response.text();

    if (!response.ok) {
        const message =
            typeof body === "object" &&
            body?.message
                ? body.message
                : `Request failed with status ${response.status}`;

        throw new Error(message);
    }

    return body;
}


async function getIncident(
    incidentId
) {
    return apiRequest(
        `/incidents/${encodeURIComponent(
            incidentId
        )}`
    );
}


async function getTimeline(
    incidentId
) {
    return apiRequest(
        `/incidents/${encodeURIComponent(
            incidentId
        )}/timeline`
    );
}


async function getEvidence(
    incidentId
) {
    return apiRequest(
        `/incidents/${encodeURIComponent(
            incidentId
        )}/evidence`
    );
}


async function getRecommendations(
    incidentId
) {
    return apiRequest(
        `/incidents/${encodeURIComponent(
            incidentId
        )}/recommendations`
    );
}


async function getDiagnosis(
    incidentId
) {
    return apiRequest(
        `/incidents/${encodeURIComponent(
            incidentId
        )}/diagnosis`
    );
}


async function dryRunRemediation(
    payload
) {
    return apiRequest(
        "/remediation/dry-run",
        {
            method: "POST",
            body: JSON.stringify(
                payload
            ),
        }
    );
}


async function executeRemediation(
    payload
) {
    return apiRequest(
        "/remediation/execute",
        {
            method: "POST",
            body: JSON.stringify(
                payload
            ),
        }
    );
}


/*
 * Expose API functions to the frontend application.
 */
window.getIncident =
    getIncident;

window.getTimeline =
    getTimeline;

window.getEvidence =
    getEvidence;

window.getRecommendations =
    getRecommendations;

window.getDiagnosis =
    getDiagnosis;

window.dryRunRemediation =
    dryRunRemediation;

window.executeRemediation =
    executeRemediation;