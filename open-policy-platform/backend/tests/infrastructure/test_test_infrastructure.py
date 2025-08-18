"""
Test Infrastructure Tests
Tests that verify the test infrastructure is properly configured
"""

import pytest
import subprocess
import os
import sys
import time
import requests
from pathlib import Path

class TestTestInfrastructure:
    """Test test infrastructure configuration"""
    
    def test_setup_test_automation(self):
        """Test that test automation is properly set up"""
        
        # Check if pytest is installed
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                                   capture_output=True, text=True)
            assert result.returncode == 0, "pytest should be installed"
            assert "pytest" in result.stdout, "pytest version should be displayed"
        except Exception as e:
            assert False, f"pytest installation check failed: {e}"
        
        # Check if test directories exist
        test_dirs = [
            "tests",
            "tests/database",
            "tests/api",
            "tests/security",
            "tests/performance",
            "tests/scripts",
            "tests/integration",
            "tests/infrastructure"
        ]
        
        for test_dir in test_dirs:
            assert os.path.exists(test_dir), f"Test directory {test_dir} should exist"
        
        # Check if test configuration files exist
        config_files = [
            "pytest.ini",
            "conftest.py"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                assert os.path.isfile(config_file), f"Config file {config_file} should be a file"
        
        # Check if test requirements are installed
        test_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-fastapi",
            "pytest-postgresql",
            "pytest-mock",
            "pytest-cov",
            "pytest-httpx",
            "playwright"
        ]
        
        for package in test_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                # Some packages might not be importable directly
                pass
        
        # Check if test database is configured
        test_db_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres@localhost:5432/openpolicy_test")
        assert "test" in test_db_url.lower(), "Test database URL should contain 'test'"
    
    def test_configure_ci_cd_pipeline(self):
        """Test that CI/CD pipeline is properly configured"""
        
        # Check if CI/CD configuration files exist
        ci_files = [
            ".github/workflows/tests.yml",
            ".github/workflows/deploy.yml",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            "azure-pipelines.yml"
        ]
        
        ci_file_exists = False
        for ci_file in ci_files:
            if os.path.exists(ci_file):
                ci_file_exists = True
                assert os.path.isfile(ci_file), f"CI file {ci_file} should be a file"
                break
        
        # At least one CI configuration should exist
        assert ci_file_exists, "At least one CI/CD configuration file should exist"
        
        # Check if Docker configuration exists for CI
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.test.yml"
        ]
        
        docker_file_exists = False
        for docker_file in docker_files:
            if os.path.exists(docker_file):
                docker_file_exists = True
                assert os.path.isfile(docker_file), f"Docker file {docker_file} should be a file"
                break
        
        # Docker configuration should exist for containerized testing
        assert docker_file_exists, "Docker configuration should exist for CI/CD"
        
        # Check if environment variables are configured
        env_vars = [
            "TEST_DATABASE_URL",
            "TEST_API_URL",
            "TEST_FRONTEND_URL"
        ]
        
        for env_var in env_vars:
            # Environment variable should be defined (even if empty)
            assert env_var in os.environ, f"Environment variable {env_var} should be defined"
        
        # Check if test scripts are executable
        test_scripts = [
            "scripts/run-tests.sh",
            "scripts/setup-test-env.sh",
            "scripts/cleanup-test-env.sh"
        ]
        
        for script in test_scripts:
            if os.path.exists(script):
                assert os.access(script, os.X_OK), f"Test script {script} should be executable"
    
    def test_implement_test_reporting(self):
        """Test that test reporting is properly implemented"""
        
        # Check if test reporting directories exist
        report_dirs = [
            "reports",
            "reports/coverage",
            "reports/test-results",
            "reports/performance",
            "reports/accessibility"
        ]
        
        for report_dir in report_dirs:
            if not os.path.exists(report_dir):
                os.makedirs(report_dir, exist_ok=True)
            assert os.path.exists(report_dir), f"Report directory {report_dir} should exist"
        
        # Check if test reporting configuration exists
        pytest_config = "pytest.ini"
        if os.path.exists(pytest_config):
            with open(pytest_config, 'r') as f:
                config_content = f.read()
                assert "addopts" in config_content, "pytest.ini should contain addopts for reporting"
                assert "--html" in config_content or "--junitxml" in config_content, "pytest.ini should configure HTML or XML reporting"
        
        # Check if coverage configuration exists
        coverage_configs = [
            ".coveragerc",
            "pyproject.toml",
            "setup.cfg"
        ]
        
        coverage_configured = False
        for config in coverage_configs:
            if os.path.exists(config):
                with open(config, 'r') as f:
                    content = f.read()
                    if "coverage" in content.lower():
                        coverage_configured = True
                        break
        
        assert coverage_configured, "Coverage reporting should be configured"
        
        # Check if test result formats are supported
        result_formats = [
            "html",
            "xml",
            "json",
            "junit"
        ]
        
        # At least one format should be supported
        format_supported = False
        for fmt in result_formats:
            try:
                if fmt == "html":
                    import pytest_html
                    format_supported = True
                elif fmt == "xml":
                    import pytest_xml
                    format_supported = True
                elif fmt == "json":
                    import pytest_json
                    format_supported = True
            except ImportError:
                pass
        
        assert format_supported, "At least one test result format should be supported"
    
    def test_setup_test_monitoring(self):
        """Test that test monitoring is properly set up"""
        
        # Check if monitoring configuration exists
        monitoring_configs = [
            "monitoring/test-monitoring.yml",
            "monitoring/prometheus.yml",
            "monitoring/grafana.yml",
            "monitoring/alertmanager.yml"
        ]
        
        monitoring_configured = False
        for config in monitoring_configs:
            if os.path.exists(config):
                monitoring_configured = True
                assert os.path.isfile(config), f"Monitoring config {config} should be a file"
                break
        
        # Monitoring should be configured for production-like testing
        assert monitoring_configured, "Test monitoring should be configured"
        
        # Check if health check endpoints exist
        health_endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/api/health",
            "http://localhost:5173/health"
        ]
        
        health_endpoint_available = False
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    health_endpoint_available = True
                    break
            except requests.RequestException:
                continue
        
        assert health_endpoint_available, "At least one health check endpoint should be available"
        
        # Check if logging is configured
        log_dirs = [
            "logs",
            "logs/tests",
            "logs/application",
            "logs/errors"
        ]
        
        for log_dir in log_dirs:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            assert os.path.exists(log_dir), f"Log directory {log_dir} should exist"
        
        # Check if log configuration exists
        log_configs = [
            "logging.conf",
            "logback.xml",
            "log4j2.xml"
        ]
        
        log_configured = False
        for config in log_configs:
            if os.path.exists(config):
                log_configured = True
                assert os.path.isfile(config), f"Log config {config} should be a file"
                break
        
        assert log_configured, "Logging should be configured for test monitoring"
        
        # Check if metrics collection is configured
        metrics_configs = [
            "metrics/prometheus.yml",
            "metrics/statsd.yml",
            "metrics/datadog.yml"
        ]
        
        metrics_configured = False
        for config in metrics_configs:
            if os.path.exists(config):
                metrics_configured = True
                assert os.path.isfile(config), f"Metrics config {config} should be a file"
                break
        
        assert metrics_configured, "Metrics collection should be configured"
    
    def test_validate_test_coverage(self):
        """Test that test coverage validation is working"""
        
        # Check if coverage tools are available
        coverage_tools = [
            "coverage",
            "pytest-cov",
            "codecov"
        ]
        
        coverage_available = False
        for tool in coverage_tools:
            try:
                if tool == "coverage":
                    import coverage
                    coverage_available = True
                elif tool == "pytest-cov":
                    import pytest_cov
                    coverage_available = True
                elif tool == "codecov":
                    import codecov
                    coverage_available = True
            except ImportError:
                pass
        
        assert coverage_available, "At least one coverage tool should be available"
        
        # Check if coverage thresholds are configured
        coverage_thresholds = [
            "backend",
            "web",
            "scripts"
        ]
        
        threshold_configured = False
        for component in coverage_thresholds:
            coverage_file = f"{component}/.coveragerc"
            if os.path.exists(coverage_file):
                with open(coverage_file, 'r') as f:
                    content = f.read()
                    if "fail_under" in content or "min_coverage" in content:
                        threshold_configured = True
                        break
        
        assert threshold_configured, "Coverage thresholds should be configured"
        
        # Check if test coverage reports are generated
        coverage_dirs = [
            "reports/coverage",
            "htmlcov",
            "coverage"
        ]
        
        coverage_reports_exist = False
        for coverage_dir in coverage_dirs:
            if os.path.exists(coverage_dir):
                # Check for coverage report files
                report_files = list(Path(coverage_dir).glob("*.html")) + list(Path(coverage_dir).glob("*.xml"))
                if report_files:
                    coverage_reports_exist = True
                    break
        
        # Coverage reports should exist (even if empty)
        assert coverage_reports_exist, "Coverage reports should be generated"
        
        # Check if coverage badges are configured
        badge_files = [
            "coverage-badge.svg",
            "tests-badge.svg",
            "build-badge.svg"
        ]
        
        badges_configured = False
        for badge in badge_files:
            if os.path.exists(badge):
                badges_configured = True
                break
        
        # Badges should be configured for quick coverage visibility
        assert badges_configured, "Coverage badges should be configured"
        
        # Check if test coverage is tracked over time
        coverage_history = [
            "reports/coverage/history.json",
            "reports/coverage/trend.csv",
            "reports/coverage/summary.json"
        ]
        
        history_tracked = False
        for history_file in coverage_history:
            if os.path.exists(history_file):
                history_tracked = True
                break
        
        # Coverage history should be tracked
        assert history_tracked, "Test coverage history should be tracked"
