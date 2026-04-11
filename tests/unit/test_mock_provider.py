"""
Unit tests for mock LLM provider.
"""

import pytest
from arcnical.review.llm.mock_provider import MockLLMProvider
from arcnical.review.llm.base import ReviewResult


class TestMockLLMProvider:
    """Test mock provider for testing"""

    def test_init_default(self):
        """Should initialize with defaults"""
        provider = MockLLMProvider()

        assert provider.deterministic is True
        assert provider.findings_count == 3
        assert provider.call_count == 0

    def test_init_custom(self):
        """Should initialize with custom values"""
        provider = MockLLMProvider(deterministic=False, findings_count=5)

        assert provider.deterministic is False
        assert provider.findings_count == 5

    def test_get_provider_name(self):
        """Should return 'mock' as provider name"""
        provider = MockLLMProvider()
        assert provider.get_provider_name() == "mock"

    def test_get_model_name(self):
        """Should return mock model name"""
        provider = MockLLMProvider()
        assert provider.get_model_name() == "mock-model"

    def test_validate_config(self):
        """Should always validate successfully"""
        provider = MockLLMProvider()
        assert provider.validate_config() is True

    def test_health_check(self):
        """Should always pass health check"""
        provider = MockLLMProvider()
        assert provider.health_check() is True

    def test_review_code_returns_result(self):
        """Should return ReviewResult"""
        provider = MockLLMProvider()

        result = provider.review_code("test code", {}, {})

        assert isinstance(result, ReviewResult)
        assert result.provider == "mock"
        assert result.model == "mock-model"
        assert result.confidence == 0.9

    def test_review_code_findings_count(self):
        """Should return correct number of findings"""
        provider = MockLLMProvider(findings_count=5)

        result = provider.review_code("test code", {}, {})

        assert len(result.findings) == 5

    def test_review_code_deterministic(self):
        """Should return same findings on each call (deterministic)"""
        provider = MockLLMProvider(deterministic=True, findings_count=2)

        result1 = provider.review_code("code1", {}, {})
        result2 = provider.review_code("code2", {}, {})

        assert len(result1.findings) == len(result2.findings)
        assert result1.findings[0]["id"] == result2.findings[0]["id"]

    def test_review_code_increments_call_count(self):
        """Should increment call count on each call"""
        provider = MockLLMProvider()

        assert provider.call_count == 0

        provider.review_code("code", {}, {})
        assert provider.call_count == 1

        provider.review_code("code", {}, {})
        assert provider.call_count == 2

    def test_review_code_recommendations(self):
        """Should generate recommendations from findings"""
        provider = MockLLMProvider(findings_count=3)

        result = provider.review_code("test code", {}, {})

        assert len(result.recommendations) == 3
        assert all(isinstance(r, str) for r in result.recommendations)

    def test_reset(self):
        """Should reset call count"""
        provider = MockLLMProvider()

        provider.review_code("code", {}, {})
        assert provider.call_count == 1

        provider.reset()
        assert provider.call_count == 0

    def test_findings_have_required_fields(self):
        """Mock findings should have required fields"""
        provider = MockLLMProvider(findings_count=1)

        result = provider.review_code("test code", {}, {})
        finding = result.findings[0]

        assert "id" in finding
        assert "description" in finding
        assert "severity" in finding
        assert "category" in finding
        assert "line_number" in finding
        assert "file" in finding

    def test_token_usage_scales_with_findings(self):
        """Token usage should scale with findings count"""
        provider1 = MockLLMProvider(findings_count=1)
        provider2 = MockLLMProvider(findings_count=5)

        result1 = provider1.review_code("code", {}, {})
        result2 = provider2.review_code("code", {}, {})

        assert result1.tokens_used < result2.tokens_used
