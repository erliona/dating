"""
Test monitoring configuration files for validity and completeness.
"""

import pytest

pytestmark = pytest.mark.integration

import json
from pathlib import Path

import yaml  # type: ignore[import]


def test_loki_config_exists():
    """Test that Loki configuration file exists."""
    config_path = Path("monitoring/loki/loki-config.yml")
    assert config_path.exists(), "Loki config file should exist"


def test_loki_config_valid_yaml():
    """Test that Loki configuration is valid YAML."""
    config_path = Path("monitoring/loki/loki-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "Loki config should be valid YAML"


def test_loki_config_modern_schema():
    """Test that Loki uses modern configuration schema."""
    config_path = Path("monitoring/loki/loki-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Check for modern schema configuration
    assert "schema_config" in config, "Should have schema_config"
    assert "configs" in config["schema_config"], "Should have schema configs"

    # Check for TSDB schema
    schema_configs = config["schema_config"]["configs"]
    assert len(schema_configs) > 0, "Should have at least one schema config"
    assert schema_configs[0]["store"] == "tsdb", "Should use TSDB store"
    assert schema_configs[0]["schema"] == "v13", "Should use schema v13"


def test_loki_config_no_deprecated_fields():
    """Test that Loki config doesn't contain deprecated fields."""
    config_path = Path("monitoring/loki/loki-config.yml")
    with open(config_path) as f:
        content = f.read()

    # These fields were deprecated and should not be present
    assert (
        "max_transfer_retries" not in content
    ), "Should not have deprecated max_transfer_retries"
    assert (
        "enforce_metric_name" not in content
    ), "Should not have deprecated enforce_metric_name"


def test_loki_config_has_storage_config():
    """Test that Loki has proper storage configuration."""
    config_path = Path("monitoring/loki/loki-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "storage_config" in config, "Should have storage_config"
    assert "tsdb_shipper" in config["storage_config"], "Should have tsdb_shipper config"


def test_loki_config_has_compactor():
    """Test that Loki has compactor configured for retention."""
    config_path = Path("monitoring/loki/loki-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "compactor" in config, "Should have compactor"
    assert (
        config["compactor"]["retention_enabled"] is True
    ), "Retention should be enabled"


def test_promtail_config_exists():
    """Test that Promtail configuration file exists."""
    config_path = Path("monitoring/promtail/promtail-config.yml")
    assert config_path.exists(), "Promtail config file should exist"


def test_promtail_config_valid_yaml():
    """Test that Promtail configuration is valid YAML."""
    config_path = Path("monitoring/promtail/promtail-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "Promtail config should be valid YAML"


def test_promtail_config_has_enhanced_features():
    """Test that Promtail has enhanced log processing features."""
    config_path = Path("monitoring/promtail/promtail-config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Check for batching configuration
    assert "clients" in config, "Should have clients config"
    assert len(config["clients"]) > 0, "Should have at least one client"
    client = config["clients"][0]
    assert "batchwait" in client, "Should have batchwait for batching"
    assert "batchsize" in client, "Should have batchsize for batching"
    assert "backoff_config" in client, "Should have retry backoff config"


def test_prometheus_config_exists():
    """Test that Prometheus configuration file exists."""
    config_path = Path("monitoring/prometheus/prometheus.yml")
    assert config_path.exists(), "Prometheus config file should exist"


def test_prometheus_config_valid_yaml():
    """Test that Prometheus configuration is valid YAML."""
    config_path = Path("monitoring/prometheus/prometheus.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "Prometheus config should be valid YAML"


def test_prometheus_config_has_loki_scraping():
    """Test that Prometheus is configured to scrape Loki metrics."""
    config_path = Path("monitoring/prometheus/prometheus.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "scrape_configs" in config, "Should have scrape_configs"

    # Check for Loki job
    job_names = [job["job_name"] for job in config["scrape_configs"]]
    assert "loki" in job_names, "Should have loki scrape job"


def test_prometheus_config_has_enhanced_labeling():
    """Test that Prometheus scrape configs have enhanced labels."""
    config_path = Path("monitoring/prometheus/prometheus.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Check that at least one job has labels
    has_labels = False
    for job in config["scrape_configs"]:
        if "static_configs" in job:
            for static_config in job["static_configs"]:
                if "labels" in static_config:
                    has_labels = True
                    break

    assert has_labels, "At least one scrape config should have labels"


def test_grafana_datasources_config_exists():
    """Test that Grafana datasources configuration exists."""
    config_path = Path("monitoring/grafana/provisioning/datasources/datasources.yml")
    assert config_path.exists(), "Grafana datasources config should exist"


def test_grafana_datasources_valid_yaml():
    """Test that Grafana datasources configuration is valid YAML."""
    config_path = Path("monitoring/grafana/provisioning/datasources/datasources.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "Grafana datasources config should be valid YAML"


def test_grafana_has_prometheus_and_loki():
    """Test that Grafana has both Prometheus and Loki datasources."""
    config_path = Path("monitoring/grafana/provisioning/datasources/datasources.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "datasources" in config, "Should have datasources"
    datasource_names = [ds["name"] for ds in config["datasources"]]

    assert "Prometheus" in datasource_names, "Should have Prometheus datasource"
    assert "Loki" in datasource_names, "Should have Loki datasource"


def test_grafana_dashboards_exist():
    """Test that Grafana dashboard files exist."""
    dashboard_dir = Path("monitoring/grafana/dashboards")
    assert dashboard_dir.exists(), "Dashboard directory should exist"

    # Check for expected dashboards
    expected_dashboards = [
        "1-infrastructure-overview.json",
        "2-application-services.json",
        "3-application-logs.json",
        "4-database-metrics.json",
    ]

    for dashboard in expected_dashboards:
        dashboard_path = dashboard_dir / dashboard
        assert dashboard_path.exists(), f"Dashboard {dashboard} should exist"


def test_grafana_dashboards_valid_json():
    """Test that all Grafana dashboards are valid JSON."""
    dashboard_dir = Path("monitoring/grafana/dashboards")

    for dashboard_file in dashboard_dir.glob("*.json"):
        with open(dashboard_file) as f:
            try:
                dashboard = json.load(f)
                assert (
                    dashboard is not None
                ), f"{dashboard_file.name} should be valid JSON"
            except json.JSONDecodeError as e:
                raise AssertionError(
                    f"{dashboard_file.name} has invalid JSON: {e}"
                ) from e


def test_docker_compose_has_version_pinning():
    """Test that docker-compose.yml uses specific versions, not :latest."""
    compose_path = Path("docker-compose.yml")
    with open(compose_path) as f:
        content = f.read()

    # Check that monitoring services don't use :latest
    assert "grafana/loki:latest" not in content, "Loki should not use :latest tag"
    assert (
        "grafana/promtail:latest" not in content
    ), "Promtail should not use :latest tag"
    assert "grafana/grafana:latest" not in content, "Grafana should not use :latest tag"
    assert (
        "prom/prometheus:latest" not in content
    ), "Prometheus should not use :latest tag"


def test_docker_compose_has_env_expansion_flag():
    """Test that Loki has -config.expand-env=true flag."""
    compose_path = Path("docker-compose.yml")
    with open(compose_path) as f:
        content = f.read()

    assert (
        "-config.expand-env=true" in content
    ), "Should have config.expand-env flag for Loki"


def test_docker_compose_has_health_checks():
    """Test that monitoring services have health checks."""
    compose_path = Path("docker-compose.yml")
    with open(compose_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})

    # Check that key monitoring services have health checks
    services_to_check = ["loki", "prometheus", "grafana", "promtail"]

    for service_name in services_to_check:
        if service_name in services:
            service = services[service_name]
            assert "healthcheck" in service, f"{service_name} should have a healthcheck"
            assert (
                "test" in service["healthcheck"]
            ), f"{service_name} healthcheck should have a test"


def test_monitoring_documentation_updated():
    """Test that monitoring documentation exists and mentions v3.0."""
    doc_path = Path("docs/MONITORING_SETUP.md")
    assert doc_path.exists(), "MONITORING_SETUP.md should exist"

    with open(doc_path) as f:
        content = f.read()

    # Check for version mentions
    assert "3.0.0" in content, "Should mention Loki 3.0.0"
    assert (
        "v2.51.0" in content or "2.51.0" in content
    ), "Should mention Prometheus version"
    assert "10.4.0" in content, "Should mention Grafana version"

    # Check for modern features
    assert "TSDB" in content or "tsdb" in content, "Should mention TSDB"
    assert "health" in content.lower(), "Should mention health checks"
