from unittest.mock import MagicMock, patch

from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_pods():
    mock_pods = MagicMock()
    mock_pods.items = []

    with patch("collectors.kubernetes_collector.config.load_kube_config"), \
         patch("collectors.kubernetes_collector.client.CoreV1Api") as mock_core, \
         patch("collectors.kubernetes_collector.client.AppsV1Api"):

        mock_core.return_value.list_pod_for_all_namespaces.return_value = mock_pods

        collector = KubernetesCollector()
        evidence = collector.collect_pods()

        assert evidence == []
        mock_core.return_value.list_pod_for_all_namespaces.assert_called_once()