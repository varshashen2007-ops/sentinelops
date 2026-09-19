from datetime import datetime, timezone

from correlation.dependency_graph import (
    DependencyGraphBuilder,
    DependencyNode,
)
from models.evidence import Evidence


def make_evidence(
    source,
    evidence_type,
    data,
    namespace="default",
    resource="test-pod",
):
    return Evidence(
        source=source,
        evidence_type=evidence_type,
        timestamp=datetime.now(timezone.utc),
        namespace=namespace,
        resource=resource,
        data=data,
    )


def test_node_identity_is_stable():
    node1 = DependencyNode(
        kind="Pod",
        name="nginx",
        namespace="default",
    )

    node2 = DependencyNode(
        kind="Pod",
        name="nginx",
        namespace="default",
    )

    assert node1.node_id == node2.node_id
    assert node1 == node2


def test_kubernetes_node_pod_container_relationship():
    evidence = make_evidence(
        "kubernetes",
        "event",
        {
            "node": "minikube",
            "pod": "nginx",
            "container": "nginx",
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    node = graph.get_node(
        "Node",
        "minikube",
        "default",
    )

    pod = graph.get_node(
        "Pod",
        "nginx",
        "default",
    )

    container = graph.get_node(
        "Container",
        "nginx",
        "default",
    )

    assert node is not None
    assert pod is not None
    assert container is not None

    relationships = {
        (
            edge.source.kind,
            edge.source.name,
            edge.target.kind,
            edge.target.name,
            edge.relationship,
        )
        for edge in graph.edges
    }

    assert (
        "Node",
        "minikube",
        "Pod",
        "nginx",
        "hosts",
    ) in relationships

    assert (
        "Pod",
        "nginx",
        "Container",
        "nginx",
        "contains",
    ) in relationships


def test_service_routes_to_pod():
    evidence = make_evidence(
        "kubernetes",
        "service",
        {
            "service": "nginx-service",
            "pod": "nginx",
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    service = graph.get_node(
        "Service",
        "nginx-service",
        "default",
    )

    pod = graph.get_node(
        "Pod",
        "nginx",
        "default",
    )

    assert service is not None
    assert pod is not None

    edge = next(
        edge
        for edge in graph.edges
        if edge.relationship == "routes_to"
    )

    assert edge.source == service
    assert edge.target == pod


def test_jaeger_service_exposes_endpoint():
    evidence = make_evidence(
        "jaeger",
        "trace",
        {
            "service_name": "sentinel-api",
            "operation_name": "GET /api",
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    service = graph.get_node(
        "Service",
        "sentinel-api",
        "default",
    )

    endpoint = graph.get_node(
        "Endpoint",
        "GET /api",
        "default",
    )

    assert service is not None
    assert endpoint is not None

    edge = next(
        edge
        for edge in graph.edges
        if edge.relationship == "exposes"
    )

    assert edge.source == service
    assert edge.target == endpoint


def test_prometheus_evidence_attaches_to_pod():
    evidence = make_evidence(
        "prometheus",
        "metric",
        {
            "metric_name": "cpu_usage",
            "value": 0.95,
            "labels": {
                "namespace": "default",
                "pod": "nginx",
                "node": "minikube",
            },
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    pod = graph.get_node(
        "Pod",
        "nginx",
        "default",
    )

    assert pod is not None
    assert evidence in pod.evidence


def test_loki_evidence_attaches_to_container():
    evidence = make_evidence(
        "loki",
        "log",
        {
            "message": "application error",
            "labels": {
                "namespace": "default",
                "pod": "nginx",
                "container": "nginx",
            },
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    container = graph.get_node(
        "Container",
        "nginx",
        "default",
    )

    assert container is not None
    assert evidence in container.evidence


def test_duplicate_nodes_are_merged():
    evidence1 = make_evidence(
        "prometheus",
        "metric",
        {
            "metric_name": "cpu_usage",
            "value": 0.5,
            "labels": {
                "namespace": "default",
                "pod": "nginx",
            },
        },
    )

    evidence2 = make_evidence(
        "loki",
        "log",
        {
            "message": "hello",
            "labels": {
                "namespace": "default",
                "pod": "nginx",
            },
        },
    )

    graph = DependencyGraphBuilder().build(
        [evidence1, evidence2]
    )

    pod = graph.get_node(
        "Pod",
        "nginx",
        "default",
    )

    assert pod is not None
    assert len(pod.evidence) == 2


def test_neighbors_returns_connected_nodes():
    evidence = make_evidence(
        "kubernetes",
        "event",
        {
            "node": "minikube",
            "pod": "nginx",
        },
    )

    graph = DependencyGraphBuilder().build([evidence])

    node = graph.get_node(
        "Node",
        "minikube",
        "default",
    )

    pod = graph.get_node(
        "Pod",
        "nginx",
        "default",
    )

    assert node is not None
    assert pod is not None

    neighbors = graph.neighbors(node)

    assert pod in neighbors