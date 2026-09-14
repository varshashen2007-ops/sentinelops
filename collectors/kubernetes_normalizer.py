from typing import Any

from models.evidence import Evidence
from models.kubernetes import (
    ContainerSnapshot,
    ContainerState,
    ContainerTermination,
    DeploymentSnapshot,
    KubernetesEvent,
    NodeSnapshot,
    PodCondition,
    PodSnapshot,
    ServicePort,
    ServiceSnapshot,
)


class KubernetesNormalizer:
    """Convert generic Kubernetes Evidence into typed normalized snapshots."""

    @staticmethod
    def normalize_pod(evidence: Evidence) -> PodSnapshot:
        data = evidence.data

        containers = [
            ContainerSnapshot(
                name=container["name"],
                ready=container.get("ready", False),
                restart_count=container.get("restart_count", 0),
                state=KubernetesNormalizer._normalize_container_state(
                    container.get("state")
                ),
                last_state=KubernetesNormalizer._normalize_container_state(
                    container.get("last_state")
                ),
            )
            for container in data.get("containers", [])
        ]

        conditions = {
            condition_type: PodCondition(**condition_data)
            for condition_type, condition_data in data.get(
                "conditions", {}
            ).items()
        }

        return PodSnapshot(
            name=evidence.resource or "unknown",
            namespace=evidence.namespace or "default",
            phase=data.get("phase"),
            pod_ip=data.get("pod_ip"),
            node_name=data.get("node_name"),
            containers=containers,
            conditions=conditions,
        )

    @staticmethod
    def normalize_deployment(evidence: Evidence) -> DeploymentSnapshot:
        data = evidence.data

        return DeploymentSnapshot(
            name=evidence.resource or "unknown",
            namespace=evidence.namespace or "default",
            desired_replicas=data.get("desired_replicas") or 0,
            available_replicas=data.get("available_replicas") or 0,
            ready_replicas=data.get("ready_replicas") or 0,
            updated_replicas=data.get("updated_replicas") or 0,
        )

    @staticmethod
    def normalize_service(evidence: Evidence) -> ServiceSnapshot:
        data = evidence.data

        ports = [
            ServicePort(
                name=port.get("name"),
                port=port["port"],
                target_port=port.get("target_port", ""),
                protocol=port.get("protocol", "TCP"),
            )
            for port in data.get("ports", [])
        ]

        return ServiceSnapshot(
            name=evidence.resource or "unknown",
            namespace=evidence.namespace or "default",
            service_type=data.get("type", "Unknown"),
            cluster_ip=data.get("cluster_ip"),
            selector=data.get("selector") or {},
            ports=ports,
        )

    @staticmethod
    def normalize_node(evidence: Evidence) -> NodeSnapshot:
        data = evidence.data

        return NodeSnapshot(
            name=evidence.resource or "unknown",
            ready=data.get("ready"),
            memory_pressure=data.get("memory_pressure"),
            disk_pressure=data.get("disk_pressure"),
            pid_pressure=data.get("pid_pressure"),
            unschedulable=data.get("unschedulable", False),
            capacity_cpu=data.get("capacity_cpu"),
            capacity_memory=data.get("capacity_memory"),
            allocatable_cpu=data.get("allocatable_cpu"),
            allocatable_memory=data.get("allocatable_memory"),
        )

    @staticmethod
    def normalize_event(evidence: Evidence) -> KubernetesEvent:
        data = evidence.data

        return KubernetesEvent(
            reason=data.get("reason"),
            message=data.get("message"),
            event_type=data.get("type"),
            count=data.get("count"),
            kind=data.get("kind"),
            resource=evidence.resource,
            namespace=evidence.namespace,
            timestamp=evidence.timestamp,
        )

    @staticmethod
    def normalize(
        evidence: Evidence,
    ) -> (
        PodSnapshot
        | DeploymentSnapshot
        | ServiceSnapshot
        | NodeSnapshot
        | KubernetesEvent
    ):
        """Normalize one Evidence object according to its evidence type."""

        normalizers = {
            "pod": KubernetesNormalizer.normalize_pod,
            "deployment": KubernetesNormalizer.normalize_deployment,
            "service": KubernetesNormalizer.normalize_service,
            "node": KubernetesNormalizer.normalize_node,
            "event": KubernetesNormalizer.normalize_event,
        }

        normalizer = normalizers.get(evidence.evidence_type)

        if normalizer is None:
            raise ValueError(
                f"Unsupported Kubernetes evidence type: "
                f"{evidence.evidence_type}"
            )

        return normalizer(evidence)

    @staticmethod
    def normalize_all(
        evidence: list[Evidence],
    ) -> list[
        PodSnapshot
        | DeploymentSnapshot
        | ServiceSnapshot
        | NodeSnapshot
        | KubernetesEvent
    ]:
        """Normalize a collection of Kubernetes evidence objects."""

        return [
            KubernetesNormalizer.normalize(item)
            for item in evidence
        ]

    @staticmethod
    def _normalize_container_state(
        state: dict[str, Any] | None,
    ) -> ContainerState:
        """Normalize a container state dictionary."""

        if not state:
            return ContainerState()

        terminated_data = state.get("terminated")

        terminated = None

        if terminated_data:
            terminated = ContainerTermination(
                reason=terminated_data.get("reason"),
                message=terminated_data.get("message"),
                exit_code=terminated_data.get("exit_code"),
                started_at=terminated_data.get("started_at"),
                finished_at=terminated_data.get("finished_at"),
            )

        return ContainerState(
            waiting=state.get("waiting"),
            running=state.get("running"),
            terminated=terminated,
        )