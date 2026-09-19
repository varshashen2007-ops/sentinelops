from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from counterfactual.approval import ApprovalRequest
from remediation.actions import ActionResult, ActionType, RemediationAction
from remediation.dry_run import DryRunValidator
from remediation.model import RemediationResult


class KubernetesRemediationClient(Protocol):
    def restart(self, target: str, namespace: str | None = None) -> Any: ...

    def scale(
        self,
        target: str,
        replicas: int,
        namespace: str | None = None,
    ) -> Any: ...

    def rollback(
        self,
        target: str,
        namespace: str | None = None,
    ) -> Any: ...

    def increase_memory(
        self,
        target: str,
        memory: str,
        namespace: str | None = None,
    ) -> Any: ...


class RemediationExecutor:
    """
    Shared remediation executor.

    Supports both SentinelOps remediation contracts:

    1. Incident-intelligence flow:
       ApprovalRequest -> RemediationResult

    2. Kubernetes infrastructure flow:
       RemediationAction -> ActionResult

    The two contracts are intentionally kept separate inside the
    executor so neither existing subsystem loses its behavior.
    """

    _SUPPORTED_ACTIONS = {
        "restart",
        "scale",
        "rollback",
        "increase_memory",
    }

    def __init__(
        self,
        kubernetes_client: KubernetesRemediationClient | None = None,
        *,
        apps_api: Any | None = None,
        dry_run_validator: DryRunValidator | None = None,
    ) -> None:
        self.kubernetes_client = kubernetes_client
        self.dry_run_validator = dry_run_validator or DryRunValidator()

        # Dhrithi's infrastructure executor supplies an AppsV1Api.
        # Import lazily so the rest of SentinelOps does not require
        # Kubernetes during simple domain-level tests.
        if apps_api is not None:
            self.apps_api = apps_api
        else:
            self.apps_api = None

    def execute(
        self,
        request_or_action: ApprovalRequest | RemediationAction,
        *,
        dry_run: bool = False,
    ) -> RemediationResult | ActionResult:
        """
        Execute either an ApprovalRequest or a RemediationAction.
        """
        if isinstance(request_or_action, ApprovalRequest):
            return self._execute_approval_request(request_or_action)

        if isinstance(request_or_action, RemediationAction):
            return self._execute_remediation_action(
                request_or_action,
                dry_run=dry_run,
            )

        raise TypeError(
            "RemediationExecutor.execute() expects "
            "ApprovalRequest or RemediationAction."
        )

    # ------------------------------------------------------------------
    # SentinelOps incident-intelligence remediation
    # ------------------------------------------------------------------

    def _execute_approval_request(
        self,
        request: ApprovalRequest,
    ) -> RemediationResult:
        if request.status != "approved":
            raise PermissionError(
                "Remediation can only be executed for an approved request."
            )

        action_type = request.action_type.lower().strip()

        if action_type not in self._SUPPORTED_ACTIONS:
            raise ValueError(
                f"Unsupported remediation action: {request.action_type}"
            )

        if not request.target or not request.target.strip():
            raise ValueError("Remediation target is required.")

        namespace = self._get_namespace(request)
        parameters = dict(request.parameters)

        self._validate_parameters(action_type, parameters)

        try:
            details = self._execute_approved_action(
                action_type,
                request.target,
                namespace,
                parameters,
            )

            return RemediationResult(
                request_id=request.request_id,
                incident_id=request.incident_id,
                action_type=request.action_type,
                target=request.target,
                status="executed",
                message="Remediation action executed successfully.",
                details=details,
            )

        except Exception as exc:
            return RemediationResult(
                request_id=request.request_id,
                incident_id=request.incident_id,
                action_type=request.action_type,
                target=request.target,
                status="failed",
                message=f"Remediation action failed: {exc}",
                details={
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

    def _validate_parameters(
        self,
        action_type: str,
        parameters: dict[str, Any],
    ) -> None:
        if action_type == "scale":
            replicas = parameters.get("replicas")

            if not isinstance(replicas, int) or isinstance(replicas, bool):
                raise ValueError(
                    "Scale remediation requires an integer 'replicas' parameter."
                )

            if replicas < 0:
                raise ValueError(
                    "Scale remediation does not allow negative replicas."
                )

        elif action_type == "increase_memory":
            memory = parameters.get("memory")

            if not isinstance(memory, str) or not memory.strip():
                raise ValueError(
                    "Memory remediation requires a non-empty 'memory' parameter."
                )

    def _execute_approved_action(
        self,
        action_type: str,
        target: str,
        namespace: str | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if self.kubernetes_client is None:
            raise RuntimeError(
                "No Kubernetes remediation client is configured."
            )

        if action_type == "restart":
            result = self.kubernetes_client.restart(
                target,
                namespace=namespace,
            )

        elif action_type == "scale":
            result = self.kubernetes_client.scale(
                target,
                replicas=parameters["replicas"],
                namespace=namespace,
            )

        elif action_type == "rollback":
            result = self.kubernetes_client.rollback(
                target,
                namespace=namespace,
            )

        elif action_type == "increase_memory":
            result = self.kubernetes_client.increase_memory(
                target,
                memory=parameters["memory"],
                namespace=namespace,
            )

        else:
            raise ValueError(
                f"Unsupported remediation action: {action_type}"
            )

        return {
            "result": result,
            "namespace": namespace,
        }

    def _get_namespace(
        self,
        request: ApprovalRequest,
    ) -> str | None:
        namespace = request.parameters.get("namespace")

        if namespace is None:
            return None

        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError(
                "Namespace must be a non-empty string when provided."
            )

        return namespace.strip()

    # ------------------------------------------------------------------
    # Dhrithi Kubernetes infrastructure remediation
    # ------------------------------------------------------------------

    def _execute_remediation_action(
        self,
        action: RemediationAction,
        *,
        dry_run: bool,
    ) -> ActionResult:
        validation = self.dry_run_validator.validate(action)

        if not validation.valid:
            return ActionResult(
                action_type=action.action_type,
                resource_type=action.resource_type,
                namespace=action.namespace,
                resource_name=action.resource_name,
                dry_run=dry_run,
                success=False,
                message=validation.message,
            )

        if dry_run:
            return ActionResult(
                action_type=action.action_type,
                resource_type=action.resource_type,
                namespace=action.namespace,
                resource_name=action.resource_name,
                dry_run=True,
                success=True,
                message=validation.message,
            )

        if self.apps_api is None:
            return ActionResult(
                action_type=action.action_type,
                resource_type=action.resource_type,
                namespace=action.namespace,
                resource_name=action.resource_name,
                dry_run=False,
                success=False,
                message="Kubernetes Apps API is not configured.",
            )

        if action.action_type is ActionType.RESTART:
            return self._restart(action)

        if action.action_type is ActionType.SCALE:
            return self._scale(action)

        if action.action_type is ActionType.ROLLBACK:
            return self._rollback(action)

        if action.action_type is ActionType.PATCH:
            return self._patch(action)

        return ActionResult(
            action_type=action.action_type,
            resource_type=action.resource_type,
            namespace=action.namespace,
            resource_name=action.resource_name,
            dry_run=False,
            success=False,
            message="Unsupported remediation action.",
        )

    def _restart(self, action: RemediationAction) -> ActionResult:
        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "sentinelops/restarted-at": datetime.now(
                                timezone.utc
                            ).isoformat()
                        }
                    }
                }
            }
        }

        self._patch_resource(action, patch)

        return self._success(action, "Restart request submitted.")

    def _scale(self, action: RemediationAction) -> ActionResult:
        patch = {
            "spec": {
                "replicas": action.parameters["replicas"]
            }
        }

        self._patch_resource(action, patch)

        return self._success(action, "Scale request submitted.")

    def _rollback(self, action: RemediationAction) -> ActionResult:
        revision = action.parameters.get("revision")

        value = str(revision) if revision is not None else "true"

        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "sentinelops/rollback-requested": value
                        }
                    }
                }
            }
        }

        self._patch_resource(action, patch)

        return self._success(action, "Rollback request submitted.")

    def _patch(self, action: RemediationAction) -> ActionResult:
        patch = action.parameters["patch"]

        self._patch_resource(action, patch)

        return self._success(action, "Patch request submitted.")

    def _patch_resource(
        self,
        action: RemediationAction,
        patch: dict[str, Any],
    ) -> Any:
        if action.resource_type.value == "deployment":
            return self.apps_api.patch_namespaced_deployment(
                name=action.resource_name,
                namespace=action.namespace,
                body=patch,
            )

        if action.resource_type.value == "statefulset":
            return self.apps_api.patch_namespaced_stateful_set(
                name=action.resource_name,
                namespace=action.namespace,
                body=patch,
            )

        raise ValueError(
            f"Unsupported resource type: {action.resource_type}"
        )

    def _success(
        self,
        action: RemediationAction,
        message: str,
    ) -> ActionResult:
        return ActionResult(
            action_type=action.action_type,
            resource_type=action.resource_type,
            namespace=action.namespace,
            resource_name=action.resource_name,
            dry_run=False,
            success=True,
            message=message,
        )