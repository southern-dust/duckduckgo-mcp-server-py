"""
Unit tests for configuration management
"""

import os
from unittest.mock import patch

import pytest

from duckduckgo_mcp_server.config import (
    DEFAULT_CONFIG,
    get_config,
    get_transport_config,
    get_rate_limiter_config,
    get_logging_config
)


class TestDefaultConfig:
    """Test cases for default configuration"""

    def test_default_config_structure(self):
        """Test that default config has expected structure"""
        assert "server" in DEFAULT_CONFIG
        assert "rate_limiter" in DEFAULT_CONFIG
        assert "logging" in DEFAULT_CONFIG
        assert "transports" in DEFAULT_CONFIG

    def test_default_server_config(self):
        """Test default server configuration"""
        server_config = DEFAULT_CONFIG["server"]
        assert "host" in server_config
        assert "http_port" in server_config
        assert "sse_port" in server_config
        assert "default_transport" in server_config

        # Check default values
        assert server_config["host"] == "0.0.0.0"
        assert server_config["http_port"] == 8080
        assert server_config["sse_port"] == 8081
        assert server_config["default_transport"] == "stdio"

    def test_default_rate_limiter_config(self):
        """Test default rate limiter configuration"""
        rate_limiter_config = DEFAULT_CONFIG["rate_limiter"]
        assert "per_second" in rate_limiter_config
        assert "per_month" in rate_limiter_config

        # Check default values
        assert rate_limiter_config["per_second"] == 1
        assert rate_limiter_config["per_month"] == 15000

    def test_default_logging_config(self):
        """Test default logging configuration"""
        logging_config = DEFAULT_CONFIG["logging"]
        assert "level" in logging_config
        assert "format" in logging_config

        # Check default values
        assert logging_config["level"] == "INFO"
        assert "%" in logging_config["format"]  # Should contain format placeholders

    def test_default_transports_config(self):
        """Test default transports configuration"""
        transports_config = DEFAULT_CONFIG["transports"]
        assert "stdio" in transports_config
        assert "http" in transports_config
        assert "sse" in transports_config
        assert "hybrid" in transports_config

        # Check each transport has expected config
        for transport_name in ["stdio", "http", "sse", "hybrid"]:
            transport_config = transports_config[transport_name]
            assert "enabled" in transport_config
            assert "description" in transport_config


class TestConfigRetrieval:
    """Test cases for configuration retrieval functions"""

    def test_get_config_default(self):
        """Test getting default configuration"""
        config = get_config()
        assert config == DEFAULT_CONFIG

    def test_get_config_with_env_vars(self):
        """Test getting configuration with environment variables"""
        # Test with custom environment variables
        env_vars = {
            "MCP_SERVER_HOST": "127.0.0.1",
            "MCP_SERVER_HTTP_PORT": "9999",
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_RATE_LIMIT_PER_SEC": "5"
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()

            # Check that environment variables override defaults
            assert config["server"]["host"] == "127.0.0.1"
            assert config["server"]["http_port"] == 9999
            assert config["logging"]["level"] == "DEBUG"
            assert config["rate_limiter"]["per_second"] == 5

    def test_get_config_invalid_env_vars(self):
        """Test handling of invalid environment variables"""
        env_vars = {
            "MCP_SERVER_HTTP_PORT": "invalid_port",  # Should be int
            "MCP_RATE_LIMIT_PER_SEC": "invalid_rate",  # Should be int
        }

        with patch.dict(os.environ, env_vars):
            # Should handle invalid values gracefully (use defaults)
            config = get_config()
            assert config["server"]["http_port"] == 8080  # Default value
            assert config["rate_limiter"]["per_second"] == 1  # Default value

    def test_get_transport_config(self):
        """Test getting transport-specific configuration"""
        # Test getting HTTP transport config
        http_config = get_transport_config("http")
        assert http_config["enabled"] is True
        assert http_config["port"] == 8080

        # Test getting SSE transport config
        sse_config = get_transport_config("sse")
        assert sse_config["enabled"] is True
        assert sse_config["port"] == 8081

        # Test getting STDIO transport config
        stdio_config = get_transport_config("stdio")
        assert stdio_config["enabled"] is True

        # Test getting hybrid transport config
        hybrid_config = get_transport_config("hybrid")
        assert hybrid_config["enabled"] is True
        assert "http_port" in hybrid_config
        assert "sse_port" in hybrid_config

    def test_get_transport_config_invalid_transport(self):
        """Test getting configuration for invalid transport"""
        with pytest.raises(ValueError):
            get_transport_config("invalid_transport")

    def test_get_rate_limiter_config(self):
        """Test getting rate limiter configuration"""
        rate_limiter_config = get_rate_limiter_config()
        assert "per_second" in rate_limiter_config
        assert "per_month" in rate_limiter_config
        assert rate_limiter_config["per_second"] >= 0
        assert rate_limiter_config["per_month"] >= 0

    def test_get_rate_limiter_config_with_env_vars(self):
        """Test getting rate limiter configuration with environment variables"""
        env_vars = {
            "MCP_RATE_LIMIT_PER_SEC": "10",
            "MCP_RATE_LIMIT_PER_MONTH": "50000"
        }

        with patch.dict(os.environ, env_vars):
            config = get_rate_limiter_config()
            assert config["per_second"] == 10
            assert config["per_month"] == 50000

    def test_get_logging_config(self):
        """Test getting logging configuration"""
        logging_config = get_logging_config()
        assert "level" in logging_config
        assert "format" in logging_config
        assert logging_config["level"] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_get_logging_config_with_env_vars(self):
        """Test getting logging configuration with environment variables"""
        env_vars = {
            "MCP_LOG_LEVEL": "DEBUG"
        }

        with patch.dict(os.environ, env_vars):
            config = get_logging_config()
            assert config["level"] == "DEBUG"

    def test_get_logging_config_invalid_level(self):
        """Test getting logging configuration with invalid level"""
        env_vars = {
            "MCP_LOG_LEVEL": "INVALID_LEVEL"
        }

        with patch.dict(os.environ, env_vars):
            # Should fall back to default level
            config = get_logging_config()
            assert config["level"] == "INFO"  # Default value


class TestConfigValidation:
    """Test cases for configuration validation"""

    def test_port_validation(self):
        """Test port number validation"""
        env_vars = {
            "MCP_SERVER_HTTP_PORT": "-1",  # Invalid negative port
            "MCP_SERVER_SSE_PORT": "65536"  # Invalid port above range
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()
            # Should use default values for invalid ports
            assert config["server"]["http_port"] == 8080
            assert config["server"]["sse_port"] == 8081

    def test_rate_limit_validation(self):
        """Test rate limit validation"""
        env_vars = {
            "MCP_RATE_LIMIT_PER_SEC": "-5",  # Invalid negative rate
            "MCP_RATE_LIMIT_PER_MONTH": "0"   # Valid zero rate
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()
            # Should handle negative values
            assert config["rate_limiter"]["per_second"] >= 0
            assert config["rate_limiter"]["per_month"] == 0

    def test_host_validation(self):
        """Test host validation"""
        env_vars = {
            "MCP_SERVER_HOST": "invalid.host.format..com"
        }

        with patch.dict(os.environ, env_vars):
            # Should still accept the host (validation might be lenient)
            config = get_config()
            assert config["server"]["host"] == "invalid.host.format..com"

    def test_transport_validation(self):
        """Test transport validation"""
        env_vars = {
            "MCP_SERVER_TRANSPORT": "invalid_transport"
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()
            # Should fall back to default transport
            assert config["server"]["default_transport"] == "stdio"


class TestConfigIntegration:
    """Integration tests for configuration management"""

    def test_config_consistency(self):
        """Test configuration consistency across components"""
        config = get_config()
        transport_config = get_transport_config("http")
        rate_limiter_config = get_rate_limiter_config()
        logging_config = get_logging_config()

        # Check that all configs are consistent
        assert config["transports"]["http"]["port"] == transport_config["port"]
        assert config["rate_limiter"]["per_second"] == rate_limiter_config["per_second"]
        assert config["logging"]["level"] == logging_config["level"]

    def test_config_immutability(self):
        """Test that returned config can be modified without affecting defaults"""
        config1 = get_config()
        config2 = get_config()

        # Modify config1
        config1["server"]["host"] = "modified.host"

        # config2 should remain unchanged
        assert config2["server"]["host"] != "modified.host"

    def test_config_overrides_priority(self):
        """Test configuration override priority (env vars > defaults)"""
        env_vars = {
            "MCP_SERVER_HOST": "env.host",
            "MCP_SERVER_HTTP_PORT": "9999",
            "MCP_LOG_LEVEL": "DEBUG"
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()

            # Environment variables should override defaults
            assert config["server"]["host"] == "env.host"
            assert config["server"]["http_port"] == 9999
            assert config["logging"]["level"] == "DEBUG"

            # Non-specified values should use defaults
            assert config["server"]["sse_port"] == 8081
            assert config["rate_limiter"]["per_second"] == 1

    def test_config_edge_cases(self):
        """Test configuration edge cases"""
        # Test empty environment variables
        env_vars = {
            "MCP_SERVER_HOST": "",
            "MCP_LOG_LEVEL": ""
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()
            # Should use defaults for empty values
            assert config["server"]["host"] == "0.0.0.0"
            assert config["logging"]["level"] == "INFO"

        # Test whitespace-only environment variables
        env_vars = {
            "MCP_SERVER_HOST": "   ",
            "MCP_LOG_LEVEL": "\t\n"
        }

        with patch.dict(os.environ, env_vars):
            config = get_config()
            # Should use defaults for whitespace-only values
            assert config["server"]["host"] == "0.0.0.0"
            assert config["logging"]["level"] == "INFO"