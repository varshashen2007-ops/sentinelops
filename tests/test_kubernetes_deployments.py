from unittest.mock import MagicMock, patch

from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_deployments():
    mock_deployments = MagicMock()
    mock_deployments.items = []

    with patch("collectors.kubernetes_collector.config.load_kube_config"), \
         patch("collectors.kubernetes_collector.client.CoreV1Api"), \
         patch("collectors.kubernetes_collector.client.AppsV1Api") as mock_apps:

        mock_apps.return_value.list_deployment_for_all_namespaces.return_value = (
            mock_deployments
        )

        collector = KubernetesCollector()
        evidence = collector.collect_deployments()

        assert evidence == []
        mock_apps.return_value.list_deployment_for_all_namespaces.assert_called_once()