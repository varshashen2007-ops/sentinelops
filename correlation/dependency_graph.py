from dataclasses import dataclass, field
from typing import Any

from models.evidence import Evidence


@dataclass
class DependencyNode:
    """
    Represents one entity in the SentinelOps dependency graph.
    """

    kind: str
    name: str
    namespace: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def node_id(self) -> str:
        """
        Generate a stable identifier for the graph node.
        """

        namespace = self.namespace or "_"

        return f"{self.kind}:{namespace}:{self.name}"

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DependencyNode):
            return NotImplemented

        return self.node_id == other.node_id


@dataclass
class DependencyEdge:
    """
    Represents a relationship between two graph nodes.
    """

    source: DependencyNode
    target: DependencyNode
    relationship: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """
    Represents the dependency/causal graph for SentinelOps.
    """

    nodes: dict[str, DependencyNode] = field(
        default_factory=dict
    )
    edges: list[DependencyEdge] = field(
        default_factory=list
    )

    def add_node(
        self,
        node: DependencyNode,
    ) -> DependencyNode:
        """
        Add a node if it does not already exist.
        """

        existing = self.nodes.get(node.node_id)

        if existing is not None:
            for item in node.evidence:
                if item not in existing.evidence:
                    existing.evidence.append(item)

            existing.metadata.update(node.metadata)

            return existing

        self.nodes[node.node_id] = node

        return node

    def add_edge(
        self,
        source: DependencyNode,
        target: DependencyNode,
        relationship: str,
        evidence: list[Evidence] | None = None,
    ) -> DependencyEdge:
        """
        Add a directed relationship between two nodes.
        """

        source = self.add_node(source)
        target = self.add_node(target)

        for edge in self.edges:
            if (
                edge.source.node_id == source.node_id
                and edge.target.node_id == target.node_id
                and edge.relationship == relationship
            ):
                if evidence:
                    for item in evidence:
                        if item not in edge.evidence:
                            edge.evidence.append(item)

                return edge

        edge = DependencyEdge(
            source=source,
            target=target,
            relationship=relationship,
            evidence=evidence or [],
        )

        self.edges.append(edge)

        return edge

    def get_node(
        self,
        kind: str,
        name: str,
        namespace: str | None = None,
    ) -> DependencyNode | None:
        """
        Retrieve a node by identity.
        """

        node_id = (
            f"{kind}:{namespace or '_'}:{name}"
        )

        return self.nodes.get(node_id)

    def neighbors(
        self,
        node: DependencyNode,
    ) -> list[DependencyNode]:
        """
        Return nodes directly connected to the given node.
        """

        result: list[DependencyNode] = []

        for edge in self.edges:
            if edge.source == node:
                result.append(edge.target)

            elif edge.target == node:
                result.append(edge.source)

        return result


class DependencyGraphBuilder:
    """
    Builds a dependency graph from normalized Kubernetes
    and observability evidence.

    Relationships are intentionally explicit and explainable.
    """

    def build(
        self,
        evidence: list[Evidence],
    ) -> DependencyGraph:

        graph = DependencyGraph()

        for item in evidence:
            self._process_evidence(
                graph,
                item,
            )

        return graph

    def _process_evidence(
        self,
        graph: DependencyGraph,
        evidence: Evidence,
    ) -> None:

        data = evidence.data or {}

        if evidence.source == "kubernetes":
            self._process_kubernetes(
                graph,
                evidence,
                data,
            )

        elif evidence.source == "prometheus":
            self._process_prometheus(
                graph,
                evidence,
                data,
            )

        elif evidence.source == "loki":
            self._process_loki(
                graph,
                evidence,
                data,
            )

        elif evidence.source == "jaeger":
            self._process_jaeger(
                graph,
                evidence,
                data,
            )

    def _process_kubernetes(
        self,
        graph: DependencyGraph,
        evidence: Evidence,
        data: dict[str, Any],
    ) -> None:
        """
        Build Kubernetes hierarchy:

        Node -> Pod -> Container

        Also supports Service -> Pod relationships.
        """

        namespace = (
            evidence.namespace
            or data.get("namespace")
        )

        pod_name = (
            data.get("pod")
            or data.get("pod_name")
            or evidence.resource
        )

        node_name = (
            data.get("node")
            or data.get("node_name")
        )

        container_name = (
            data.get("container")
            or data.get("container_name")
        )

        service_name = (
            data.get("service")
            or data.get("service_name")
        )

        if node_name and pod_name:
            node = DependencyNode(
                kind="Node",
                name=str(node_name),
                namespace=namespace,
                evidence=[evidence],
            )

            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_edge(
                node,
                pod,
                "hosts",
                [evidence],
            )

        if pod_name and container_name:
            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            container = DependencyNode(
                kind="Container",
                name=str(container_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_edge(
                pod,
                container,
                "contains",
                [evidence],
            )

        if service_name and pod_name:
            service = DependencyNode(
                kind="Service",
                name=str(service_name),
                namespace=namespace,
                evidence=[evidence],
            )

            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_edge(
                service,
                pod,
                "routes_to",
                [evidence],
            )

    def _process_prometheus(
        self,
        graph: DependencyGraph,
        evidence: Evidence,
        data: dict[str, Any],
    ) -> None:
        """
        Attach Prometheus evidence to the corresponding
        Kubernetes entity.
        """

        labels = data.get("labels", {})

        if not isinstance(labels, dict):
            labels = {}

        namespace = (
            labels.get("namespace")
            or evidence.namespace
        )

        pod_name = (
            labels.get("pod")
            or evidence.resource
        )

        node_name = (
            labels.get("node")
            or labels.get("node_name")
        )

        if pod_name:
            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_node(pod)

        if node_name:
            node = DependencyNode(
                kind="Node",
                name=str(node_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_node(node)

    def _process_loki(
        self,
        graph: DependencyGraph,
        evidence: Evidence,
        data: dict[str, Any],
    ) -> None:
        """
        Attach Loki log evidence to its Pod/container.
        """

        labels = data.get("labels", {})

        if not isinstance(labels, dict):
            labels = {}

        namespace = (
            labels.get("namespace")
            or evidence.namespace
        )

        pod_name = (
            labels.get("pod")
            or evidence.resource
        )

        container_name = labels.get("container")

        if pod_name:
            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_node(pod)

        if pod_name and container_name:
            pod = DependencyNode(
                kind="Pod",
                name=str(pod_name),
                namespace=namespace,
                evidence=[evidence],
            )

            container = DependencyNode(
                kind="Container",
                name=str(container_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_edge(
                pod,
                container,
                "contains",
                [evidence],
            )

    def _process_jaeger(
        self,
        graph: DependencyGraph,
        evidence: Evidence,
        data: dict[str, Any],
    ) -> None:
        """
        Represent application/service relationships from traces.
        """

        service_name = (
            data.get("service_name")
            or data.get("service")
        )

        operation_name = (
            data.get("operation_name")
            or data.get("operation")
        )

        namespace = evidence.namespace

        if service_name:
            service = DependencyNode(
                kind="Service",
                name=str(service_name),
                namespace=namespace,
                evidence=[evidence],
            )

            graph.add_node(service)

            if operation_name:
                endpoint = DependencyNode(
                    kind="Endpoint",
                    name=str(operation_name),
                    namespace=namespace,
                    evidence=[evidence],
                )

                graph.add_edge(
                    service,
                    endpoint,
                    "exposes",
                    [evidence],
                )