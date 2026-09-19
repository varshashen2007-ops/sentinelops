from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kubernetes import client

from remediation.actions import (
    ActionResult,
    ActionType,
    RemediationAction,
    ResourceType,
)
from remediation.dry_run import DryRunValidator


class RemediationExecutor:
    """Executes validated Kubernetes remediation actions.

    No shell commands or arbitrary kubectl invocations are used.
    """

    def __init__(
        self,
        apps_api: Any | None = None,
        dry_run_validator: DryRunValidator | None = None,
    ) -> None:
        self.apps_api = apps_api or client.AppsV1Api()
        self.dry_run_validator = dry_run_validator or DryRunValidator()

    def execute(
        self,
        action: RemediationAction,
        *,
        dry_run: bool = False,
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
        timestamp = datetime.now(timezone.utc).isoformat()

        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "sentinelops/restarted-at": timestamp,
                        }
                    }
                }
            }
        }

        self._patch_resource(action, patch)

        return self._success(
            action,
            "Resource restart requested.",
        )

    def _scale(self, action: RemediationAction) -> ActionResult:
        replicas = action.parameters["replicas"]

        patch = {
            "spec": {
                "replicas": replicas,
            }
        }

        self._patch_resource(action, patch)

        return self._success(
            action,
            f"Resource scaled to {replicas} replicas.",
            {"replicas": replicas},
        )

    def _rollback(self, action: RemediationAction) -> ActionResult:
        revision = action.parameters.get("revision")

        if revision is None:
            patch = {
                "metadata": {
                    "annotations": {
                        "sentinelops/rollback-requested": "true",
                    }
                }
            }
        else:
            patch = {
                "metadata": {
                    "annotations": {
                        "sentinelops/rollback-requested": str(revision),
                    }
                }
            }

        self._patch_resource(action, patch)

        details = {}

        if revision is not None:
            details["revision"] = revision

        return self._success(
            action,
            "Rollback request recorded on the Kubernetes resource.",
            details,
        )

    def _patch(self, action: RemediationAction) -> ActionResult:
        patch = action.parameters["patch"]

        self._patch_resource(action, patch)

        return self._success(
            action,
            "Kubernetes resource patched successfully.",
        )

    def _patch_resource(
        self,
        action: RemediationAction,
        patch: dict[str, Any],
    ) -> None:
        if action.resource_type is ResourceType.DEPLOYMENT:
            self.apps_api.patch_namespaced_deployment(
                name=action.resource_name,
                namespace=action.namespace,
                body=patch,
            )
            return

        if action.resource_type is ResourceType.STATEFULSET:
            self.apps_api.patch_namespaced_stateful_set(
                name=action.resource_name,
                namespace=action.namespace,
                body=patch,
            )
            return

        raise ValueError(
            f"Unsupported resource type: {action.resource_type}"
        )

    @staticmethod
    def _success(
        action: RemediationAction,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ActionResult:
        return ActionResult(
            action_type=action.action_type,
            resource_type=action.resource_type,
            namespace=action.namespace,
            resource_name=action.resource_name,
            dry_run=False,
            success=True,
            message=message,
            details=details or {},
        )