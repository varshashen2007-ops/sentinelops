from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContainerTermination(BaseModel):
    """Normalized information about a container's current or previous termination."""

    reason: str | None = None
    message: str | None = None
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ContainerState(BaseModel):
    """Normalized runtime state of a container."""

    waiting: dict[str, Any] | None = None
    running: dict[str, Any] | None = None
    terminated: ContainerTermination | None = None


class ContainerSnapshot(BaseModel):
    """Normalized snapshot of a Kubernetes container."""

    name: str
    ready: bool = False
    restart_count: int = 0
    state: ContainerState = Field(default_factory=ContainerState)
    last_state: ContainerState = Field(default_factory=ContainerState)


class PodCondition(BaseModel):
    """Normalized Kubernetes pod condition."""

    status: str
    reason: str | None = None
    message: str | None = None
    last_transition_time: datetime | None = None


class PodSnapshot(BaseModel):
    """Normalized snapshot of a Kubernetes pod."""

    name: str
    namespace: str
    phase: str | None = None
    pod_ip: str | None = None
    node_name: str | None = None
    containers: list[ContainerSnapshot] = Field(default_factory=list)
    conditions: dict[str, PodCondition] = Field(default_factory=dict)


class DeploymentSnapshot(BaseModel):
    """Normalized snapshot of a Kubernetes deployment."""

    name: str
    namespace: str
    desired_replicas: int = 0
    available_replicas: int = 0
    ready_replicas: int = 0
    updated_replicas: int = 0


class ServicePort(BaseModel):
    """Normalized Kubernetes service port."""

    name: str | None = None
    port: int
    target_port: str
    protocol: str


class ServiceSnapshot(BaseModel):
    """Normalized snapshot of a Kubernetes service."""

    name: str
    namespace: str
    service_type: str
    cluster_ip: str | None = None
    selector: dict[str, str] = Field(default_factory=dict)
    ports: list[ServicePort] = Field(default_factory=list)


class NodeSnapshot(BaseModel):
    """Normalized snapshot of a Kubernetes node."""

    name: str
    ready: str | None = None
    memory_pressure: str | None = None
    disk_pressure: str | None = None
    pid_pressure: str | None = None
    unschedulable: bool = False
    capacity_cpu: str | None = None
    capacity_memory: str | None = None
    allocatable_cpu: str | None = None
    allocatable_memory: str | None = None


class KubernetesEvent(BaseModel):
    """Normalized Kubernetes event."""

    reason: str | None = None
    message: str | None = None
    event_type: str | None = None
    count: int | None = None
    kind: str | None = None
    resource: str | None = None
    namespace: str | None = None
    timestamp: datetime