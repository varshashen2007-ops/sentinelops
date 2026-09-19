from unittest.mock import MagicMock, patch

from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_services():
    mock_services = MagicMock()
    mock_services.items = []

    with patch("collectors.kubernetes_collector.config.load_kube_config"), \
         patch("collectors.kubernetes_collector.client.CoreV1Api") as mock_core, \
         patch("collectors.kubernetes_collector.client.AppsV1Api"):

        mock_core.return_value.list_service_for_all_namespaces.return_value = (
            mock_services
        )

        collector = KubernetesCollector()
        evidence = collector.collect_services()

        assert evidence == []
        mock_core.return_value.list_service_for_all_namespaces.assert_called_once()