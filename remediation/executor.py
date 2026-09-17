from typing import Any, Protocol

from counterfactual.approval import ApprovalRequest
from remediation.model import RemediationResult


class KubernetesRemediationClient(Protocol):
    """
    Interface for Kubernetes mutations used by the remediation executor.
    """

    def restart(
        self,
        target: str,
        namespace: str | None = None,
    ) -> Any:
        ...

    def scale(
        self,
        target: str,
        replicas: int,
        namespace: str | None = None,
    ) -> Any:
        ...

    def rollback(
        self,
        target: str,
        namespace: str | None = None,
    ) -> Any:
        ...

    def increase_memory(
        self,
        target: str,
        memory: str,
        namespace: str | None = None,
    ) -> Any:
        ...


class RemediationExecutor:
    """
    Executes approved Kubernetes remediation actions.

    Safety boundary:
    - pending requests cannot execute
    - rejected requests cannot execute
    - only approved requests can reach the Kubernetes client
    - unsupported actions are rejected
    - invalid parameters are rejected before execution
    """

    _SUPPORTED_ACTIONS = {
        "restart",
        "scale",
        "rollback",
        "increase_memory",
    }

    def __init__(
        self,
        kubernetes_client: KubernetesRemediationClient,
    ) -> None:
        self.kubernetes_client = kubernetes_client

    def execute(
        self,
        request: ApprovalRequest,
    ) -> RemediationResult:
        if request.status != "approved":
            raise PermissionError(
                "Remediation can only be executed for an approved "
                "approval request."
            )

        action_type = request.action_type.lower().strip()

        if action_type not in self._SUPPORTED_ACTIONS:
            raise ValueError(
                f"Unsupported remediation action: "
                f"{request.action_type}"
            )

        if not request.target or not request.target.strip():
            raise ValueError(
                "A remediation target is required."
            )

        namespace = self._get_namespace(request)
        parameters = dict(request.parameters)

        # Validate the requested action before allowing any
        # Kubernetes client call.
        self._validate_parameters(
            action_type=action_type,
            parameters=parameters,
        )

        try:
            details = self._execute_action(
                action_type=action_type,
                target=request.target,
                namespace=namespace,
                parameters=parameters,
            )

            return RemediationResult(
                request_id=request.request_id,
                incident_id=request.incident_id,
                action_type=request.action_type,
                target=request.target,
                status="executed",
                message=(
                    f"Remediation action '{request.action_type}' "
                    "executed successfully."
                ),
                details=details if isinstance(details, dict) else {},
            )

        except Exception as exc:
            return RemediationResult(
                request_id=request.request_id,
                incident_id=request.incident_id,
                action_type=request.action_type,
                target=request.target,
                status="failed",
                message=(
                    f"Remediation action '{request.action_type}' "
                    f"failed: {exc}"
                ),
                details={
                    "error_type": type(exc).__name__,
                },
            )

    @staticmethod
    def _validate_parameters(
        action_type: str,
        parameters: dict[str, Any],
    ) -> None:
        if action_type == "scale":
            replicas = parameters.get("replicas")

            if not isinstance(replicas, int):
                raise ValueError(
                    "Scale remediation requires an integer "
                    "'replicas' parameter."
                )

            if replicas < 0:
                raise ValueError(
                    "Scale replicas cannot be negative."
                )

        if action_type == "increase_memory":
            memory = parameters.get("memory")

            if not isinstance(memory, str) or not memory.strip():
                raise ValueError(
                    "Memory remediation requires a non-empty "
                    "'memory' parameter."
                )

    def _execute_action(
        self,
        action_type: str,
        target: str,
        namespace: str | None,
        parameters: dict[str, Any],
    ) -> Any:
        if action_type == "restart":
            return self.kubernetes_client.restart(
                target=target,
                namespace=namespace,
            )

        if action_type == "scale":
            return self.kubernetes_client.scale(
                target=target,
                replicas=parameters["replicas"],
                namespace=namespace,
            )

        if action_type == "rollback":
            return self.kubernetes_client.rollback(
                target=target,
                namespace=namespace,
            )

        if action_type == "increase_memory":
            return self.kubernetes_client.increase_memory(
                target=target,
                memory=parameters["memory"],
                namespace=namespace,
            )

        raise ValueError(
            f"Unsupported remediation action: {action_type}"
        )

    @staticmethod
    def _get_namespace(
        request: ApprovalRequest,
    ) -> str | None:
        namespace = request.parameters.get("namespace")

        if namespace is None:
            return None

        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError(
                "Namespace must be a non-empty string when provided."
            )

        return namespace
