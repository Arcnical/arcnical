"""
Unit tests for CLI provider integration.

Tests for:
- Provider configuration loading
- CLI flag parsing
- Provider creation and validation
- L4 integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from arcnical.cli.config import ProviderConfigLoader
from arcnical.orchestrator.l4_integration import L4Integration
from arcnical.review.llm.mock_provider import MockLLMProvider
from arcnical.review.llm.base import ProviderError


class TestProviderConfigLoader:
    """Test ProviderConfigLoader"""

    def test_init_no_config_file(self):
        """Should initialize when no config file exists"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")
        assert loader.config_path is None or loader.config == {}

    def test_get_provider_config_defaults(self):
        """Should return default config for provider"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")
        config = loader.get_provider_config("claude")

        assert config["api_key"] is None  # No key set
        assert config["model"] == "claude-sonnet-4-6"
        assert config["temperature"] == 0
        assert config["max_tokens"] == 4000

    def test_get_provider_config_with_api_key(self):
        """Should use provided API key"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")
        config = loader.get_provider_config("claude", api_key="test-key")

        assert config["api_key"] == "test-key"

    def test_get_provider_config_with_model_override(self):
        """Should override model if provided"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")
        config = loader.get_provider_config("claude", model="claude-opus-4-6")

        assert config["model"] == "claude-opus-4-6"

    def test_validate_config_missing_api_key(self):
        """Should fail validation without API key"""
        loader = ProviderConfigLoader()
        config = {"model": "test"}

        assert loader.validate_config("claude", config) is False

    def test_validate_config_missing_model(self):
        """Should fail validation without model"""
        loader = ProviderConfigLoader()
        config = {"api_key": "test"}

        assert loader.validate_config("claude", config) is False

    def test_validate_config_success(self):
        """Should pass validation with required fields"""
        loader = ProviderConfigLoader()
        config = {"api_key": "test-key", "model": "test-model"}

        assert loader.validate_config("claude", config) is True

    def test_get_env_key_for_provider_claude(self):
        """Should get ANTHROPIC_API_KEY for Claude"""
        loader = ProviderConfigLoader()
        assert loader._get_env_key_for_provider("claude") == "ANTHROPIC_API_KEY"

    def test_get_env_key_for_provider_openai(self):
        """Should get OPENAI_API_KEY for OpenAI"""
        loader = ProviderConfigLoader()
        assert loader._get_env_key_for_provider("openai") == "OPENAI_API_KEY"

    def test_get_env_key_for_provider_gemini(self):
        """Should get GOOGLE_API_KEY for Gemini"""
        loader = ProviderConfigLoader()
        assert loader._get_env_key_for_provider("gemini") == "GOOGLE_API_KEY"

    def test_get_default_model_claude(self):
        """Should return default Claude model"""
        loader = ProviderConfigLoader()
        assert loader._get_default_model("claude") == "claude-sonnet-4-6"

    def test_get_default_model_openai(self):
        """Should return default OpenAI model"""
        loader = ProviderConfigLoader()
        assert loader._get_default_model("openai") == "gpt-4-turbo"

    def test_get_default_model_gemini(self):
        """Should return default Gemini model"""
        loader = ProviderConfigLoader()
        assert loader._get_default_model("gemini") == "gemini-pro"

    def test_get_provider_config_with_env_var(self):
        """Should load API key from environment variable"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = loader.get_provider_config("claude")
            assert config["api_key"] == "env-key"

    def test_cli_flag_overrides_env_var(self):
        """Should prefer CLI flag over environment variable"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = loader.get_provider_config("claude", api_key="cli-key")
            assert config["api_key"] == "cli-key"


class TestL4Integration:
    """Test L4Integration"""

    def test_create_l4_agent(self):
        """Should create L4 agent with provider"""
        provider = MockLLMProvider()
        agent = L4Integration.create_l4_agent(provider)

        assert agent is not None
        assert agent.get_provider_name() == "mock"

    def test_create_l4_agent_with_none_provider(self):
        """Should raise ValueError with None provider"""
        with pytest.raises(ValueError):
            L4Integration.create_l4_agent(None)

    def test_verify_provider_health(self):
        """Should check provider health"""
        provider = MockLLMProvider()
        is_healthy = L4Integration.verify_provider_health(provider)

        assert is_healthy is True

    def test_verify_provider_health_failure(self):
        """Should handle provider health check failure"""
        provider = Mock()
        provider.get_provider_name = Mock(return_value="mock")
        provider.health_check = Mock(return_value=False)

        is_healthy = L4Integration.verify_provider_health(provider)

        assert is_healthy is False

    def test_run_l4_review(self):
        """Should run L4 review with agent"""
        provider = MockLLMProvider()
        agent = L4Integration.create_l4_agent(provider)

        # Create mock report
        mock_report = Mock()
        mock_report.recommendations = []
        mock_report.metadata = None
        mock_report.findings_count = 0

        # Mock the agent's review method
        agent.review = Mock(return_value=mock_report)

        result = L4Integration.run_l4_review(agent, mock_report)

        assert result == mock_report
        agent.review.assert_called_once_with(mock_report)

    def test_run_l4_review_with_metadata(self):
        """Should update report metadata with provider info"""
        provider = MockLLMProvider()
        agent = L4Integration.create_l4_agent(provider)

        # Create mock report with metadata
        mock_metadata = Mock()
        mock_metadata.model = None

        mock_report = Mock()
        mock_report.recommendations = []
        mock_report.metadata = mock_metadata
        mock_report.findings_count = 0

        # Mock the agent's review method
        agent.review = Mock(return_value=mock_report)

        result = L4Integration.run_l4_review(agent, mock_report)

        # Should update metadata
        assert result.metadata.model == "mock-model"

    def test_run_l4_review_error_handling(self):
        """Should handle errors during L4 review"""
        provider = MockLLMProvider()
        agent = L4Integration.create_l4_agent(provider)

        mock_report = Mock()

        # Mock the agent's review method to raise error
        agent.review = Mock(side_effect=Exception("Review failed"))

        with pytest.raises(Exception):
            L4Integration.run_l4_review(agent, mock_report)


class TestProviderFlagIntegration:
    """Integration tests for provider flags in CLI"""

    def test_provider_flag_choices(self):
        """Provider flag should only accept valid providers"""
        # Valid: claude, openai, gemini
        # Invalid: others
        from arcnical.review.llm.provider_factory import LLMProviderFactory

        valid = LLMProviderFactory.list_providers()
        assert "claude" in valid
        assert "openai" in valid
        assert "gemini" in valid

    def test_api_key_from_environment(self):
        """Should read API key from environment variable"""
        loader = ProviderConfigLoader()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            config = loader.get_provider_config("claude")
            assert config["api_key"] == "sk-test"

    def test_config_precedence(self):
        """Should follow config precedence: CLI > ENV > File"""
        loader = ProviderConfigLoader(config_path="/nonexistent/path.yaml")

        # File has no config, ENV has key, CLI overrides
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            # CLI flag wins
            config = loader.get_provider_config("claude", api_key="cli-key")
            assert config["api_key"] == "cli-key"

            # ENV used when no CLI flag
            config = loader.get_provider_config("claude")
            assert config["api_key"] == "env-key"

    def test_health_check_integration(self):
        """Should integrate health check into provider setup"""
        provider = MockLLMProvider()
        is_healthy = L4Integration.verify_provider_health(provider)

        assert is_healthy is True
