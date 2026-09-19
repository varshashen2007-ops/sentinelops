from unittest.mock import Mock

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.remediation_routes import (
    configure_remediation_service,
)
from remediation.actions import (
    ActionType,
    ResourceType,
)
from remediation.audit import AuditLog
from remediation.service import RemediationService


def create_test_service() -> tuple[RemediationService, Mock]:
    executor = Mock()

    executor.execute.side_effect = lambda action, dry_run=False: Mock(
        action_type=action.action_type,
        resource_type=action.resource_type,
        namespace=action.namespace,
        resource_name=action.resource_name,
        dry_run=dry_run,
        success=True,
        message="Remediation action completed.",
        details={},
    )

    service = RemediationService(
        executor=executor,
        audit_log=AuditLog(),
    )

    return service, executor


service, mock_executor = create_test_service()

configure_remediation_service(service)

client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_remediation_dry_run_endpoint_exists() -> None:
    response = client.post(
        "/remediation/dry-run",
        json={
            "action_type": "restart",
            "resource_type": "deployment",
            "namespace": "default",
            "resource_name": "web",
            "parameters": {},
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["action_type"] == "restart"
    assert body["resource_type"] == "deployment"
    assert body["namespace"] == "default"
    assert body["resource_name"] == "web"
    assert body["dry_run"] is True
    assert body["success"] is True


def test_remediation_execute_endpoint_exists() -> None:
    response = client.post(
        "/remediation/execute",
        json={
            "action_type": "restart",
            "resource_type": "deployment",
            "namespace": "default",
            "resource_name": "web",
            "parameters": {},
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["action_type"] == "restart"
    assert body["resource_type"] == "deployment"
    assert body["namespace"] == "default"
    assert body["resource_name"] == "web"
    assert body["dry_run"] is False
    assert body["success"] is True


def test_remediation_rejects_empty_namespace() -> None:
    response = client.post(
        "/remediation/dry-run",
        json={
            "action_type": "restart",
            "resource_type": "deployment",
            "namespace": "",
            "resource_name": "web",
            "parameters": {},
        },
    )

    assert response.status_code == 422


def test_remediation_rejects_empty_resource_name() -> None:
    response = client.post(
        "/remediation/dry-run",
        json={
            "action_type": "restart",
            "resource_type": "deployment",
            "namespace": "default",
            "resource_name": "",
            "parameters": {},
        },
    )

    assert response.status_code == 422


def test_remediation_accepts_parameters() -> None:
    response = client.post(
        "/remediation/dry-run",
        json={
            "action_type": "scale",
            "resource_type": "deployment",
            "namespace": "default",
            "resource_name": "web",
            "parameters": {
                "replicas": 3,
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["action_type"] == "scale"
    assert body["dry_run"] is True
    assert body["success"] is True


def test_execute_passes_action_to_service() -> None:
    mock_executor.reset_mock()

    response = client.post(
        "/remediation/execute",
        json={
            "action_type": "scale",
            "resource_type": "deployment",
            "namespace": "production",
            "resource_name": "api",
            "parameters": {
                "replicas": 4,
            },
        },
    )

    assert response.status_code == 200

    mock_executor.execute.assert_called_once()

    action = mock_executor.execute.call_args.args[0]

    assert action.action_type is ActionType.SCALE
    assert action.resource_type is ResourceType.DEPLOYMENT
    assert action.namespace == "production"
    assert action.resource_name == "api"
    assert action.parameters == {"replicas": 4}