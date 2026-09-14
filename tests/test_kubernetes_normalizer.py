from datetime import datetime, timezone

from collectors.kubernetes_normalizer import KubernetesNormalizer
from models.evidence import Evidence
from models.kubernetes import (
    DeploymentSnapshot,
    KubernetesEvent,
    NodeSnapshot,
    PodSnapshot,
    ServiceSnapshot,
)


def test_normalize_pod():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="pod",
        timestamp=datetime.now(timezone.utc),
        namespace="default",
        resource="test-pod",
        data={
            "phase": "Running",
            "pod_ip": "10.0.0.10",
            "node_name": "minikube",
            "containers": [
                {
                    "name": "app",
                    "ready": True,
                    "restart_count": 2,
                    "state": {
                        "waiting": None,
                        "running": {"started_at": None},
                        "terminated": None,
                    },
                    "last_state": {
                        "waiting": None,
                        "running": None,
                        "terminated": {
                            "reason": "Error",
                            "message": "previous failure",
                            "exit_code": 1,
                            "started_at": None,
                            "finished_at": None,
                        },
                    },
                }
            ],
            "conditions": {
                "Ready": {
                    "status": "True",
                    "reason": None,
                    "message": None,
                    "last_transition_time": None,
                }
            },
        },
    )

    result = KubernetesNormalizer.normalize_pod(evidence)

    assert isinstance(result, PodSnapshot)
    assert result.name == "test-pod"
    assert result.namespace == "default"
    assert result.phase == "Running"
    assert result.pod_ip == "10.0.0.10"
    assert result.node_name == "minikube"

    assert len(result.containers) == 1
    assert result.containers[0].name == "app"
    assert result.containers[0].ready is True
    assert result.containers[0].restart_count == 2

    assert result.containers[0].last_state.terminated is not None
    assert result.containers[0].last_state.terminated.reason == "Error"
    assert result.containers[0].last_state.terminated.exit_code == 1

    assert "Ready" in result.conditions
    assert result.conditions["Ready"].status == "True"


def test_normalize_deployment():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="deployment",
        timestamp=datetime.now(timezone.utc),
        namespace="default",
        resource="nginx-demo",
        data={
            "desired_replicas": 3,
            "available_replicas": 2,
            "ready_replicas": 2,
            "updated_replicas": 3,
        },
    )

    result = KubernetesNormalizer.normalize_deployment(evidence)

    assert isinstance(result, DeploymentSnapshot)
    assert result.name == "nginx-demo"
    assert result.namespace == "default"
    assert result.desired_replicas == 3
    assert result.available_replicas == 2
    assert result.ready_replicas == 2
    assert result.updated_replicas == 3


def test_normalize_service():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="service",
        timestamp=datetime.now(timezone.utc),
        namespace="default",
        resource="nginx-service",
        data={
            "type": "NodePort",
            "cluster_ip": "10.111.18.123",
            "selector": {"app": "nginx"},
            "ports": [
                {
                    "name": None,
                    "port": 80,
                    "target_port": "80",
                    "protocol": "TCP",
                }
            ],
        },
    )

    result = KubernetesNormalizer.normalize_service(evidence)

    assert isinstance(result, ServiceSnapshot)
    assert result.name == "nginx-service"
    assert result.namespace == "default"
    assert result.service_type == "NodePort"
    assert result.cluster_ip == "10.111.18.123"
    assert result.selector == {"app": "nginx"}

    assert len(result.ports) == 1
    assert result.ports[0].port == 80
    assert result.ports[0].target_port == "80"
    assert result.ports[0].protocol == "TCP"


def test_normalize_node():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="node",
        timestamp=datetime.now(timezone.utc),
        namespace=None,
        resource="minikube",
        data={
            "ready": "True",
            "memory_pressure": "False",
            "disk_pressure": "False",
            "pid_pressure": "False",
            "unschedulable": False,
            "capacity_cpu": "12",
            "capacity_memory": "7971472Ki",
            "allocatable_cpu": "12",
            "allocatable_memory": "7971472Ki",
        },
    )

    result = KubernetesNormalizer.normalize_node(evidence)

    assert isinstance(result, NodeSnapshot)
    assert result.name == "minikube"
    assert result.ready == "True"
    assert result.memory_pressure == "False"
    assert result.disk_pressure == "False"
    assert result.pid_pressure == "False"
    assert result.unschedulable is False
    assert result.capacity_cpu == "12"
    assert result.allocatable_cpu == "12"


def test_normalize_event():
    timestamp = datetime.now(timezone.utc)

    evidence = Evidence(
        source="kubernetes",
        evidence_type="event",
        timestamp=timestamp,
        namespace="monitoring",
        resource="test-pod",
        data={
            "reason": "BackOff",
            "message": "Back-off restarting failed container",
            "type": "Warning",
            "count": 5,
            "kind": "Pod",
        },
    )

    result = KubernetesNormalizer.normalize_event(evidence)

    assert isinstance(result, KubernetesEvent)
    assert result.reason == "BackOff"
    assert result.message == "Back-off restarting failed container"
    assert result.event_type == "Warning"
    assert result.count == 5
    assert result.kind == "Pod"
    assert result.resource == "test-pod"
    assert result.namespace == "monitoring"
    assert result.timestamp == timestamp


def test_normalize_all_preserves_count():
    evidence = [
        Evidence(
            source="kubernetes",
            evidence_type="deployment",
            timestamp=datetime.now(timezone.utc),
            namespace="default",
            resource="test-deployment",
            data={
                "desired_replicas": 1,
                "available_replicas": 1,
                "ready_replicas": 1,
                "updated_replicas": 1,
            },
        ),
        Evidence(
            source="kubernetes",
            evidence_type="node",
            timestamp=datetime.now(timezone.utc),
            namespace=None,
            resource="minikube",
            data={
                "ready": "True",
                "memory_pressure": "False",
                "disk_pressure": "False",
                "pid_pressure": "False",
                "unschedulable": False,
                "capacity_cpu": "12",
                "capacity_memory": "7971472Ki",
                "allocatable_cpu": "12",
                "allocatable_memory": "7971472Ki",
            },
        ),
    ]

    result = KubernetesNormalizer.normalize_all(evidence)

    assert len(result) == len(evidence)
    assert isinstance(result[0], DeploymentSnapshot)
    assert isinstance(result[1], NodeSnapshot)


def test_normalize_unknown_evidence_type_raises_error():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="unknown",
        timestamp=datetime.now(timezone.utc),
        namespace="default",
        resource="something",
        data={},
    )

    try:
        KubernetesNormalizer.normalize(evidence)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported Kubernetes evidence type" in str(exc)