"""
Unit tests for LLM base classes and exceptions.
"""

import pytest
from arcnical.review.llm.base import (
    LLMProvider,
    ReviewResult,
    ProviderError,
    ProviderUnavailableError,
    ProviderConfigError,
    ProviderTimeoutError,
)


class TestProviderExceptions:
    """Test exception hierarchy"""

    def test_provider_error_is_exception(self):
        """ProviderError should be an Exception"""
        assert issubclass(ProviderError, Exception)

    def test_provider_unavailable_error_is_provider_error(self):
        """ProviderUnavailableError should inherit from ProviderError"""
        assert issubclass(ProviderUnavailableError, ProviderError)

    def test_provider_config_error_is_provider_error(self):
        """ProviderConfigError should inherit from ProviderError"""
        assert issubclass(ProviderConfigError, ProviderError)

    def test_provider_timeout_error_is_provider_error(self):
        """ProviderTimeoutError should inherit from ProviderError"""
        assert issubclass(ProviderTimeoutError, ProviderError)

    def test_raise_provider_error(self):
        """Should be able to raise ProviderError"""
        with pytest.raises(ProviderError):
            raise ProviderError("test error")

    def test_raise_provider_unavailable_error(self):
        """Should be able to raise ProviderUnavailableError"""
        with pytest.raises(ProviderUnavailableError):
            raise ProviderUnavailableError("API unavailable")


class TestReviewResult:
    """Test ReviewResult dataclass"""

    def test_create_review_result(self):
        """Should create ReviewResult with all fields"""
        result = ReviewResult(
            findings=[{"id": "1", "description": "test"}],
            recommendations=["recommendation 1"],
            confidence=0.85,
            provider="test",
            model="test-model",
            tokens_used=100,
            latency_seconds=1.5,
        )

        assert result.findings == [{"id": "1", "description": "test"}]
        assert result.recommendations == ["recommendation 1"]
        assert result.confidence == 0.85
        assert result.provider == "test"
        assert result.model == "test-model"
        assert result.tokens_used == 100
        assert result.latency_seconds == 1.5

    def test_review_result_defaults(self):
        """ReviewResult should require all fields"""
        with pytest.raises(TypeError):
            # Missing required argument
            ReviewResult(findings=[])


class TestLLMProviderAbstract:
    """Test LLMProvider abstract class"""

    def test_cannot_instantiate_abstract_class(self):
        """Should not be able to instantiate abstract LLMProvider"""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            LLMProvider()

    def test_subclass_must_implement_review_code(self):
        """Subclass must implement review_code"""

        class IncompleteProv(LLMProvider):
            def get_provider_name(self):
                return "incomplete"

            def get_model_name(self):
                return "incomplete"

            def validate_config(self):
                return True

            def health_check(self):
                return True

        with pytest.raises(TypeError):
            IncompleteProv()

    def test_complete_implementation(self):
        """Complete implementation should work"""

        class CompleteProv(LLMProvider):
            def review_code(self, code_snippet, context, metrics):
                return ReviewResult(
                    findings=[],
                    recommendations=[],
                    confidence=0.9,
                    provider="complete",
                    model="test",
                    tokens_used=0,
                    latency_seconds=0.1,
                )

            def get_provider_name(self):
                return "complete"

            def get_model_name(self):
                return "test-model"

            def validate_config(self):
                return True

            def health_check(self):
                return True

        provider = CompleteProv()
        assert provider.get_provider_name() == "complete"
        assert provider.get_model_name() == "test-model"
        assert provider.validate_config() is True
        assert provider.health_check() is True

        result = provider.review_code("code", {}, {})
        assert isinstance(result, ReviewResult)
        assert result.provider == "complete"
