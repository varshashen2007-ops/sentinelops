from unittest.mock import Mock

from remediation.actions import (
    ActionType,
    RemediationAction,
    ResourceType,
)
from remediation.dry_run import DryRunValidator
from remediation.executor import RemediationExecutor


def make_action(
    action_type: ActionType,
    parameters: dict | None = None,
) -> RemediationAction:
    return RemediationAction(
        action_type=action_type,
        resource_type=ResourceType.DEPLOYMENT,
        namespace="default",
        resource_name="web",
        parameters=parameters or {},
    )


def test_restart_dry_run() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(ActionType.RESTART),
        dry_run=True,
    )

    assert result.success is True
    assert result.dry_run is True

    apps_api.patch_namespaced_deployment.assert_not_called()


def test_scale_dry_run() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(
            ActionType.SCALE,
            {"replicas": 3},
        ),
        dry_run=True,
    )

    assert result.success is True
    assert result.dry_run is True

    apps_api.patch_namespaced_deployment.assert_not_called()


def test_invalid_scale_is_rejected() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(
            ActionType.SCALE,
            {"replicas": -1},
        ),
        dry_run=True,
    )

    assert result.success is False
    assert "greater than or equal to zero" in result.message

    apps_api.patch_namespaced_deployment.assert_not_called()


def test_patch_requires_dictionary() -> None:
    validator = DryRunValidator()

    action = make_action(
        ActionType.PATCH,
        {"patch": "not-a-dictionary"},
    )

    result = validator.validate(action)

    assert result.valid is False
    assert "dictionary" in result.message


def test_restart_calls_kubernetes_api() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(ActionType.RESTART),
    )

    assert result.success is True

    apps_api.patch_namespaced_deployment.assert_called_once()

    call = apps_api.patch_namespaced_deployment.call_args

    assert call.kwargs["name"] == "web"
    assert call.kwargs["namespace"] == "default"

    patch = call.kwargs["body"]

    assert "spec" in patch
    assert "template" in patch["spec"]


def test_scale_calls_kubernetes_api() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(
            ActionType.SCALE,
            {"replicas": 5},
        ),
    )

    assert result.success is True

    apps_api.patch_namespaced_deployment.assert_called_once()

    patch = apps_api.patch_namespaced_deployment.call_args.kwargs["body"]

    assert patch["spec"]["replicas"] == 5


def test_rollback_dry_run() -> None:
    apps_api = Mock()

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(
            ActionType.ROLLBACK,
            {"revision": 4},
        ),
        dry_run=True,
    )

    assert result.success is True
    assert result.dry_run is True

    apps_api.patch_namespaced_deployment.assert_not_called()


def test_patch_calls_kubernetes_api() -> None:
    apps_api = Mock()

    patch = {
        "spec": {
            "replicas": 2,
        }
    }

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(
        make_action(
            ActionType.PATCH,
            {"patch": patch},
        ),
    )

    assert result.success is True

    apps_api.patch_namespaced_deployment.assert_called_once()

    actual_patch = (
        apps_api.patch_namespaced_deployment.call_args.kwargs["body"]
    )

    assert actual_patch == patch


def test_statefulset_scale_uses_statefulset_api() -> None:
    apps_api = Mock()

    action = RemediationAction(
        action_type=ActionType.SCALE,
        resource_type=ResourceType.STATEFULSET,
        namespace="default",
        resource_name="database",
        parameters={"replicas": 2},
    )

    executor = RemediationExecutor(apps_api=apps_api)

    result = executor.execute(action)

    assert result.success is True

    apps_api.patch_namespaced_stateful_set.assert_called_once()

    patch = apps_api.patch_namespaced_stateful_set.call_args.kwargs["body"]

    assert patch["spec"]["replicas"] == 2