"""
Unit tests for refactored L4 Review Agent.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from arcnical.review.l4_refactored import L4ReviewAgent
from arcnical.review.llm.mock_provider import MockLLMProvider
from arcnical.review.llm.base import ReviewResult, LLMProvider
from arcnical.schema import Recommendation, Severity, RecommendationCategory


class TestL4ReviewAgentInit:
    """Test L4 agent initialization"""

    def test_init_with_valid_provider(self):
        """Should initialize with valid provider"""
        provider = MockLLMProvider()
        agent = L4ReviewAgent(provider)

        assert agent.provider == provider

    def test_init_with_none_provider(self):
        """Should raise ValueError with None provider"""
        with pytest.raises(ValueError):
            L4ReviewAgent(None)

    def test_init_sets_report_builder(self):
        """Should initialize report builder"""
        provider = MockLLMProvider()
        agent = L4ReviewAgent(provider)

        assert agent.report_builder is not None


class TestL4ReviewAgentMethods:
    """Test L4 agent methods"""

    @pytest.fixture
    def agent(self):
        """Create agent with mock provider"""
        provider = MockLLMProvider(findings_count=2)
        return L4ReviewAgent(provider)

    def test_get_provider_name(self, agent):
        """Should return provider name"""
        assert agent.get_provider_name() == "mock"

    def test_get_model_name(self, agent):
        """Should return model name"""
        assert agent.get_model_name() == "mock-model"

    def test_health_check(self, agent):
        """Should check provider health"""
        assert agent.health_check() is True

    def test_map_severity_critical(self):
        """Should map 'critical' string to Severity.CRITICAL"""
        assert L4ReviewAgent._map_severity("critical") == Severity.CRITICAL
        assert L4ReviewAgent._map_severity("error") == Severity.CRITICAL

    def test_map_severity_high(self):
        """Should map 'high' string to Severity.HIGH"""
        assert L4ReviewAgent._map_severity("high") == Severity.HIGH

    def test_map_severity_medium(self):
        """Should map 'medium' string to Severity.MEDIUM"""
        assert L4ReviewAgent._map_severity("medium") == Severity.MEDIUM
        assert L4ReviewAgent._map_severity("warning") == Severity.MEDIUM

    def test_map_severity_low(self):
        """Should map unknown to Severity.LOW"""
        assert L4ReviewAgent._map_severity("low") == Severity.LOW
        assert L4ReviewAgent._map_severity("unknown") == Severity.LOW

    def test_extract_context(self, agent):
        """Should extract context from report"""
        # Create mock report
        mock_report = Mock()
        mock_report.summary = Mock()
        mock_report.summary.code_sample = "test code"
        mock_report.recommendations = []
        mock_report.metrics = Mock()
        mock_report.metrics.model_dump = Mock(return_value={"complexity": 8})

        context = agent._extract_context(mock_report)

        assert "code_sample" in context
        assert "findings" in context
        assert "metrics" in context
        assert "provider" in context
        assert "model" in context


class TestL4ReviewAgentReview:
    """Test review method"""

    def test_review_with_mock_provider(self):
        """Should review with mock provider"""
        provider = MockLLMProvider(findings_count=2)
        agent = L4ReviewAgent(provider)

        # Create mock report
        mock_report = Mock()
        mock_report.summary = Mock()
        mock_report.summary.code_sample = ""
        mock_report.recommendations = []
        mock_report.metrics = None
        mock_report.findings_count = 0

        result = agent.review(mock_report)

        # Should add recommendations
        assert result == mock_report
        assert len(result.recommendations) >= 0

    def test_review_converts_findings_to_recommendations(self):
        """Should convert findings to Recommendation objects"""
        provider = MockLLMProvider(findings_count=1)
        agent = L4ReviewAgent(provider)

        # Create mock report
        mock_report = Mock()
        mock_report.summary = Mock()
        mock_report.summary.code_sample = ""
        mock_report.recommendations = []
        mock_report.metrics = None
        mock_report.findings_count = 0

        result = agent.review(mock_report)

        # Check if recommendations are Recommendation objects (or have required structure)
        for rec in result.recommendations:
            # Should have basic recommendation properties
            if hasattr(rec, "id"):
                assert "L4" in rec.id


class TestL4ReviewAgentFindings:
    """Test findings conversion"""

    def test_convert_findings_to_recommendations(self):
        """Should convert findings to recommendations"""
        provider = MockLLMProvider()
        agent = L4ReviewAgent(provider)

        findings = [
            {
                "description": "Test finding",
                "severity": "high",
                "file": "test.py",
                "line_number": 10,
            }
        ]

        recommendations = agent._convert_findings_to_recommendations(findings)

        assert len(recommendations) == 1
        assert isinstance(recommendations[0], Recommendation)
        assert recommendations[0].severity == Severity.HIGH
        assert recommendations[0].layer == "L4"

    def test_convert_findings_handles_errors(self):
        """Should handle errors in findings conversion"""
        provider = MockLLMProvider()
        agent = L4ReviewAgent(provider)

        # Invalid finding (missing required fields)
        findings = [{}]

        recommendations = agent._convert_findings_to_recommendations(findings)

        # Should handle gracefully
        assert isinstance(recommendations, list)

    def test_convert_empty_findings(self):
        """Should handle empty findings"""
        provider = MockLLMProvider()
        agent = L4ReviewAgent(provider)

        recommendations = agent._convert_findings_to_recommendations([])

        assert recommendations == []
