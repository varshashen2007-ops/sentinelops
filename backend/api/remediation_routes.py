from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import (
    RemediationRequest,
    RemediationResponse,
)
from remediation.actions import (
    ActionType,
    RemediationAction,
    ResourceType,
)
from remediation.executor import RemediationExecutor
from remediation.service import RemediationService


router = APIRouter(
    prefix="/remediation",
    tags=["remediation"],
)


_service: RemediationService = RemediationService(
    executor=RemediationExecutor(),
)


def configure_remediation_service(
    service: RemediationService,
) -> None:
    global _service
    _service = service


def _build_action(
    request: RemediationRequest,
) -> RemediationAction:
    try:
        action_type = ActionType(request.action_type)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported action_type: {request.action_type}"
        ) from exc

    try:
        resource_type = ResourceType(request.resource_type)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported resource_type: {request.resource_type}"
        ) from exc

    return RemediationAction(
        action_type=action_type,
        resource_type=resource_type,
        namespace=request.namespace,
        resource_name=request.resource_name,
        parameters=request.parameters,
    )


def _result_response(result) -> RemediationResponse:
    return RemediationResponse(
        action_type=result.action_type.value,
        resource_type=result.resource_type.value,
        namespace=result.namespace,
        resource_name=result.resource_name,
        dry_run=result.dry_run,
        success=result.success,
        message=result.message,
        details=result.details,
    )


@router.post(
    "/dry-run",
    response_model=RemediationResponse,
)
def remediation_dry_run(
    request: RemediationRequest,
) -> RemediationResponse:
    try:
        action = _build_action(request)
    except ValueError as exc:
        return RemediationResponse(
            action_type=request.action_type,
            resource_type=request.resource_type,
            namespace=request.namespace,
            resource_name=request.resource_name,
            dry_run=True,
            success=False,
            message=str(exc),
        )

    result = _service.execute(
        action,
        requester="api",
        dry_run=True,
    )

    return _result_response(result)


@router.post(
    "/execute",
    response_model=RemediationResponse,
)
def remediation_execute(
    request: RemediationRequest,
) -> RemediationResponse:
    try:
        action = _build_action(request)
    except ValueError as exc:
        return RemediationResponse(
            action_type=request.action_type,
            resource_type=request.resource_type,
            namespace=request.namespace,
            resource_name=request.resource_name,
            dry_run=False,
            success=False,
            message=str(exc),
        )

    result = _service.execute(
        action,
        requester="api",
        dry_run=False,
    )

    return _result_response(result)