from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_frontend_files_exist() -> None:
    assert (FRONTEND / "index.html").is_file()
    assert (FRONTEND / "styles.css").is_file()
    assert (FRONTEND / "app.js").is_file()
    assert (FRONTEND / "api.js").is_file()


def test_index_loads_api_before_app() -> None:
    content = (
        FRONTEND / "index.html"
    ).read_text(encoding="utf-8")

    api_position = content.index(
        'src="api.js"'
    )

    app_position = content.index(
        'src="app.js"'
    )

    assert api_position < app_position


def test_frontend_api_contains_incident_operations() -> None:
    content = (
        FRONTEND / "api.js"
    ).read_text(encoding="utf-8")

    assert "getIncident" in content
    assert "getTimeline" in content
    assert "getEvidence" in content
    assert "getRecommendations" in content


def test_frontend_api_contains_remediation_operations() -> None:
    content = (
        FRONTEND / "api.js"
    ).read_text(encoding="utf-8")

    assert "dryRunRemediation" in content
    assert "executeRemediation" in content


def test_frontend_app_contains_incident_loading() -> None:
    content = (
        FRONTEND / "app.js"
    ).read_text(encoding="utf-8")

    assert "selectIncident" in content
    assert "getIncident" in content
    assert "getTimeline" in content
    assert "getEvidence" in content
    assert "getRecommendations" in content


def test_frontend_app_contains_remediation_controls() -> None:
    content = (
        FRONTEND / "app.js"
    ).read_text(encoding="utf-8")

    assert "getRemediationAction" in content
    assert "runDryRun" in content
    assert "executeAction" in content