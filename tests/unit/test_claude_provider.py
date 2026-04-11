"""
Unit tests for Claude provider.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from arcnical.review.llm.claude_provider import ClaudeProvider
from arcnical.review.llm.base import (
    ProviderConfigError,
    ProviderUnavailableError,
    ProviderTimeoutError,
    ReviewResult,
)


class TestClaudeProviderInit:
    """Test Claude provider initialization"""

    def test_init_with_valid_api_key(self):
        """Should initialize with valid API key"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(api_key="test-key")
            assert provider.api_key == "test-key"
            assert provider.model == "claude-sonnet-4-6"

    def test_init_without_api_key(self):
        """Should raise ProviderConfigError without API key"""
        with pytest.raises(ProviderConfigError):
            ClaudeProvider(api_key="")

    def test_init_with_custom_model(self):
        """Should initialize with custom model"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(
                api_key="test-key",
                model="claude-opus-4-6",
            )
            assert provider.model == "claude-opus-4-6"

    def test_init_with_custom_settings(self):
        """Should initialize with custom temperature and max_tokens"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(
                api_key="test-key",
                temperature=0.5,
                max_tokens=2000,
                timeout=60,
            )
            assert provider.temperature == 0.5
            assert provider.max_tokens == 2000
            assert provider.timeout == 60


class TestClaudeProviderMethods:
    """Test Claude provider methods"""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked Anthropic client"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            return ClaudeProvider(api_key="test-key")

    def test_get_provider_name(self, provider):
        """get_provider_name should return 'claude'"""
        assert provider.get_provider_name() == "claude"

    def test_get_model_name(self, provider):
        """get_model_name should return model name"""
        assert provider.get_model_name() == "claude-sonnet-4-6"

    def test_extract_severity_critical(self, provider):
        """Should extract critical severity"""
        assert provider._extract_severity("This is a critical error") == "critical"
        assert provider._extract_severity("This is an error") == "critical"

    def test_extract_severity_high(self, provider):
        """Should extract high severity"""
        assert provider._extract_severity("High priority issue") == "high"
        assert provider._extract_severity("Serious problem") == "high"

    def test_extract_severity_medium(self, provider):
        """Should extract medium severity"""
        assert provider._extract_severity("Medium warning") == "medium"
        assert provider._extract_severity("Warning: check this") == "medium"

    def test_extract_severity_low(self, provider):
        """Should extract low severity for unknown"""
        assert provider._extract_severity("Some suggestion") == "low"


class TestClaudeProviderReview:
    """Test review_code method"""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked Anthropic client"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            return ClaudeProvider(api_key="test-key")

    def test_review_code_success(self, provider):
        """Should return ReviewResult on success"""
        # Mock the API response
        mock_response = Mock()
        mock_response.content = [Mock(text="- Finding 1\n- Finding 2")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        provider.client = Mock()
        provider.client.messages.create = Mock(return_value=mock_response)

        result = provider.review_code("test code", {}, {})

        assert isinstance(result, ReviewResult)
        assert result.provider == "claude"
        assert result.tokens_used == 150
        assert len(result.findings) >= 0
        assert len(result.recommendations) >= 0

    def test_review_code_timeout(self, provider):
        """Should raise ProviderTimeoutError on timeout"""
        from anthropic import APITimeoutError

        provider.client = Mock()
        provider.client.messages.create = Mock(side_effect=APITimeoutError("timeout"))

        with pytest.raises(ProviderTimeoutError):
            provider.review_code("test code", {}, {})

    def test_review_code_connection_error(self, provider):
        """Should raise ProviderUnavailableError on connection error"""
        import httpx
        from anthropic import APIConnectionError

        provider.client = Mock()
        provider.client.messages.create = Mock(
            side_effect=APIConnectionError(
                request=httpx.Request("POST", "https://api.anthropic.com")
            )
        )

        with pytest.raises(ProviderUnavailableError):
            provider.review_code("test code", {}, {})


class TestClaudeProviderValidation:
    """Test validation and health check"""

    def test_validate_config_success(self):
        """Should return True when validation succeeds"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(api_key="test-key")

            # Mock successful validation
            mock_response = Mock()
            provider.client = Mock()
            provider.client.messages.create = Mock(return_value=mock_response)

            assert provider.validate_config() is True

    def test_validate_config_failure(self):
        """Should return False when validation fails"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(api_key="test-key")

            # Mock failed validation
            provider.client = Mock()
            provider.client.messages.create = Mock(side_effect=Exception("error"))

            assert provider.validate_config() is False

    def test_health_check(self, ):
        """health_check should call validate_config"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = ClaudeProvider(api_key="test-key")
            provider.client = Mock()
            provider.client.messages.create = Mock()

            # Health check should succeed
            assert provider.health_check() is True
