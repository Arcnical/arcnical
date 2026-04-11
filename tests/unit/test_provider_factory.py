"""
Unit tests for LLM provider factory.
"""

import pytest
from unittest.mock import patch

from arcnical.review.llm.provider_factory import LLMProviderFactory
from arcnical.review.llm.base import ProviderError, LLMProvider
from arcnical.review.llm.claude_provider import ClaudeProvider
from arcnical.review.llm.mock_provider import MockLLMProvider


class TestLLMProviderFactory:
    """Test provider factory"""

    def test_list_providers(self):
        """Should list all available providers"""
        providers = LLMProviderFactory.list_providers()

        assert isinstance(providers, list)
        assert "claude" in providers
        assert "openai" in providers
        assert "gemini" in providers

    def test_is_available_true(self):
        """Should return True for available providers"""
        assert LLMProviderFactory.is_available("claude") is True
        assert LLMProviderFactory.is_available("openai") is True
        assert LLMProviderFactory.is_available("gemini") is True

    def test_is_available_false(self):
        """Should return False for unavailable providers"""
        assert LLMProviderFactory.is_available("unknown") is False
        assert LLMProviderFactory.is_available("invalid") is False

    def test_create_claude_provider(self):
        """Should create Claude provider"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = LLMProviderFactory.create(
                "claude",
                {"api_key": "test-key"},
            )

            assert isinstance(provider, ClaudeProvider)
            assert provider.get_provider_name() == "claude"

    def test_create_unknown_provider(self):
        """Should raise error for unknown provider"""
        with pytest.raises(ProviderError) as exc_info:
            LLMProviderFactory.create("unknown", {})

        assert "Unknown provider" in str(exc_info.value)

    def test_create_provider_case_insensitive(self):
        """Provider name should be case insensitive"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider1 = LLMProviderFactory.create(
                "CLAUDE",
                {"api_key": "test-key"},
            )
            provider2 = LLMProviderFactory.create(
                "Claude",
                {"api_key": "test-key"},
            )

            assert provider1.get_provider_name() == "claude"
            assert provider2.get_provider_name() == "claude"

    def test_create_provider_with_whitespace(self):
        """Provider name should handle whitespace"""
        with patch("arcnical.review.llm.claude_provider.Anthropic"):
            provider = LLMProviderFactory.create(
                "  claude  ",
                {"api_key": "test-key"},
            )

            assert provider.get_provider_name() == "claude"

    def test_register_custom_provider(self):
        """Should be able to register custom provider"""

        class CustomProvider(LLMProvider):
            def review_code(self, code, context, metrics):
                pass

            def get_provider_name(self):
                return "custom"

            def get_model_name(self):
                return "custom-model"

            def validate_config(self):
                return True

            def health_check(self):
                return True

        LLMProviderFactory.register_provider("custom", CustomProvider)

        assert LLMProviderFactory.is_available("custom") is True
        assert "custom" in LLMProviderFactory.list_providers()

    def test_openai_not_implemented(self):
        """OpenAI provider should raise error (not implemented)"""
        with pytest.raises(ProviderError) as exc_info:
            LLMProviderFactory.create("openai", {"api_key": "test"})

        assert "not yet implemented" in str(exc_info.value)

    def test_gemini_not_implemented(self):
        """Gemini provider should raise error (not implemented)"""
        with pytest.raises(ProviderError) as exc_info:
            LLMProviderFactory.create("gemini", {"api_key": "test"})

        assert "not yet implemented" in str(exc_info.value)
