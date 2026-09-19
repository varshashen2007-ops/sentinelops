import pytest

from counterfactual.approval import ApprovalRequest
from remediation.executor import RemediationExecutor


class FakeKubernetesClient:
    def __init__(self):
        self.calls = []

    def restart(self, target, namespace=None):
        self.calls.append(("restart", target, namespace))
        return {"operation": "restart"}

    def scale(self, target, replicas, namespace=None):
        self.calls.append(("scale", target, replicas, namespace))
        return {"operation": "scale", "replicas": replicas}

    def rollback(self, target, namespace=None):
        self.calls.append(("rollback", target, namespace))
        return {"operation": "rollback"}

    def increase_memory(self, target, memory, namespace=None):
        self.calls.append(
            ("increase_memory", target, memory, namespace)
        )
        return {"operation": "increase_memory", "memory": memory}


def make_request(
    status="approved",
    action_type="restart",
    target="api-server",
    request_id="REQ-001",
):
    return ApprovalRequest(
        request_id=request_id,
        incident_id="INC-001",
        action_type=action_type,
        target=target,
        status=status,
    )


def test_approved_restart_is_executed():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    result = executor.execute(make_request())

    assert result.status == "executed"
    assert result.action_type == "restart"
    assert result.target == "api-server"
    assert client.calls == [
        ("restart", "api-server", None)
    ]


def test_pending_request_cannot_execute():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(status="pending")

    with pytest.raises(PermissionError, match="approved"):
        executor.execute(request)

    assert client.calls == []


def test_rejected_request_cannot_execute():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(status="rejected")

    with pytest.raises(PermissionError, match="approved"):
        executor.execute(request)

    assert client.calls == []


def test_approved_scale_requires_replicas():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="scale")

    with pytest.raises(ValueError, match="replicas"):
        executor.execute(request)

    assert client.calls == []


def test_approved_scale_executes_with_replicas():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="scale")
    request.parameters = {
        "replicas": 3,
        "namespace": "default",
    }

    result = executor.execute(request)

    assert result.status == "executed"
    assert client.calls == [
        ("scale", "api-server", 3, "default")
    ]


def test_negative_scale_is_rejected():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="scale")
    request.parameters = {"replicas": -1}

    with pytest.raises(ValueError, match="negative"):
        executor.execute(request)

    assert client.calls == []


def test_approved_rollback_is_executed():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="rollback")

    result = executor.execute(request)

    assert result.status == "executed"
    assert client.calls == [
        ("rollback", "api-server", None)
    ]


def test_approved_memory_increase_requires_memory():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="increase_memory")

    with pytest.raises(ValueError, match="memory"):
        executor.execute(request)

    assert client.calls == []


def test_approved_memory_increase_is_executed():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="increase_memory")
    request.parameters = {
        "memory": "512Mi",
        "namespace": "default",
    }

    result = executor.execute(request)

    assert result.status == "executed"
    assert client.calls == [
        ("increase_memory", "api-server", "512Mi", "default")
    ]


def test_unsupported_action_is_rejected():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(action_type="delete_everything")

    with pytest.raises(ValueError, match="Unsupported"):
        executor.execute(request)

    assert client.calls == []


def test_missing_target_is_rejected():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    request = make_request(target=None)

    with pytest.raises(ValueError, match="target"):
        executor.execute(request)

    assert client.calls == []


def test_kubernetes_failure_is_recorded():
    class FailingClient(FakeKubernetesClient):
        def restart(self, target, namespace=None):
            raise RuntimeError("Kubernetes API unavailable")

    client = FailingClient()
    executor = RemediationExecutor(client)

    result = executor.execute(make_request())

    assert result.status == "failed"
    assert "Kubernetes API unavailable" in result.message
    assert result.details["error_type"] == "RuntimeError"


def test_remediation_result_serializes():
    client = FakeKubernetesClient()
    executor = RemediationExecutor(client)

    result = executor.execute(make_request())

    data = result.to_dict()

    assert data["request_id"] == "REQ-001"
    assert data["incident_id"] == "INC-001"
    assert data["action_type"] == "restart"
    assert data["target"] == "api-server"
    assert data["status"] == "executed"
    assert data["executed_at"] is not None
