from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api.errors import APIError
from backend.api.request_context import create_request_id
from backend.api.remediation_routes import router as remediation_router
from backend.api.schemas import (
    DiagnosisResponse,
    ErrorResponse,
    EvidenceResponse,
    IncidentResponse,
    RecommendationResponse,
    TimelineEventResponse,
)


logger = logging.getLogger("sentinelops.api")


app = FastAPI(
    title="SentinelOps API",
    version="1.0.0",
)


app.include_router(remediation_router)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or create_request_id()
    )

    request.state.request_id = request_id

    logger.info(
        "API request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "API request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )

        return response

    except Exception:
        logger.exception(
            "API request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise


@app.exception_handler(APIError)
async def api_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        create_request_id(),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            message=exc.message,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        create_request_id(),
    )

    logger.exception(
        "Unhandled API error",
        extra={
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An internal error occurred.",
            request_id=request_id,
        ).model_dump(),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: str,
) -> IncidentResponse:
    raise APIError(
        status_code=404,
        error="not_found",
        message=(
            f"Incident '{incident_id}' was not found."
        ),
    )


@app.get(
    "/incidents/{incident_id}/timeline",
    response_model=list[TimelineEventResponse],
)
def get_timeline(
    incident_id: str,
) -> list[TimelineEventResponse]:
    return []


@app.get(
    "/incidents/{incident_id}/diagnosis",
    response_model=DiagnosisResponse,
)
def get_diagnosis(
    incident_id: str,
) -> DiagnosisResponse:
    return DiagnosisResponse(
        incident_id=incident_id,
        diagnosis=None,
        confidence=None,
    )


@app.get(
    "/incidents/{incident_id}/evidence",
    response_model=list[EvidenceResponse],
)
def get_evidence(
    incident_id: str,
) -> list[EvidenceResponse]:
    return []


@app.get(
    "/incidents/{incident_id}/recommendations",
    response_model=list[RecommendationResponse],
)
def get_recommendations(
    incident_id: str,
) -> list[RecommendationResponse]:
    return []