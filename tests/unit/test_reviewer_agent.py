"""Unit tests for Session #9: ReviewerAgent, RecommendationDocument, html_exporter."""

import json
import pytest
from unittest.mock import Mock, MagicMock
from pydantic import ValidationError

from arcnical.schema import Evidence, FileReference
from arcnical.review.reviewer_agent import ReviewerAgent
from arcnical.review.recommendation_doc import IssueDetail, RecommendationDocument
from arcnical.review.html_exporter import export_to_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(metric: str = "complexity", value: float = 8.5) -> Evidence:
    return Evidence(
        metric=metric,
        value=value,
        references=[FileReference(file="src/main.py", line=42)],
    )


def _make_report_proxy(score: float = 72.0, repo: str = "test-repo") -> object:
    scores_obj = type("Scores", (), {"overall": score})()
    summary_obj = type("Summary", (), {"repo": repo})()
    return type("ReportProxy", (), {"scores": scores_obj, "summary": summary_obj})()


def _make_provider_mock(json_response: str) -> Mock:
    """Build a mock that looks like ClaudeProvider (has .client attribute)."""
    provider = Mock()
    provider.get_model_name.return_value = "claude-sonnet-4-6"
    provider.get_provider_name.return_value = "claude"

    content_block = Mock()
    content_block.text = json_response
    api_response = Mock()
    api_response.content = [content_block]

    provider.client = Mock()
    provider.client.messages.create.return_value = api_response
    return provider


def _make_issue_detail(**overrides) -> IssueDetail:
    defaults = dict(
        id="ISS-001",
        title="Test issue",
        severity="HIGH",
        affected_files=["app.py:10"],
        description="Something is wrong",
        fix=["Fix step 1"],
        effort="Low",
        priority=1,
    )
    defaults.update(overrides)
    return IssueDetail(**defaults)


def _make_doc(**overrides) -> RecommendationDocument:
    from datetime import date, timedelta

    today = date.today().isoformat()
    defaults = dict(
        repo_name="my-repo",
        repo_url="",
        analysis_date=today,
        model_used="claude-sonnet-4-6",
        health_score=72.0,
        severity_summary={"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
        issues=[_make_issue_detail()],
        total_issues=1,
        next_review_date=(date.today() + timedelta(days=30)).isoformat(),
    )
    defaults.update(overrides)
    return RecommendationDocument(**defaults)


# ---------------------------------------------------------------------------
# Test 1: run() returns a RecommendationDocument when Claude API succeeds
# ---------------------------------------------------------------------------

class TestReviewerAgentRunReturnsDoc:
    def test_reviewer_agent_run_returns_doc(self):
        valid_json = json.dumps({
            "issues": [
                {
                    "id": "ISS-001",
                    "title": "Circular dependency detected",
                    "severity": "CRITICAL",
                    "affected_files": ["arcnical/graph/builder.py:10"],
                    "description": "Module A imports B which imports A.",
                    "fix": ["Introduce an abstraction layer", "Use dependency injection"],
                    "effort": "High",
                    "priority": 1,
                }
            ]
        })
        provider = _make_provider_mock(valid_json)
        agent = ReviewerAgent(provider)
        doc = agent.run([_make_evidence()], _make_report_proxy())

        assert isinstance(doc, RecommendationDocument)
        assert doc.total_issues == 1
        assert doc.issues[0].id == "ISS-001"
        assert doc.issues[0].severity == "CRITICAL"
        assert doc.model_used == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Test 2: fallback when API raises
# ---------------------------------------------------------------------------

class TestReviewerAgentFallback:
    def test_reviewer_agent_fallback(self):
        provider = Mock()
        provider.get_model_name.return_value = "claude-sonnet-4-6"
        provider.get_provider_name.return_value = "claude"
        # .client.messages.create raises to simulate API failure
        provider.client = Mock()
        provider.client.messages.create.side_effect = RuntimeError("API unavailable")

        agent = ReviewerAgent(provider)
        evidence = [_make_evidence("circular_dependency", 3.0), _make_evidence("complexity", 9.2)]
        doc = agent.run(evidence, _make_report_proxy())

        assert isinstance(doc, RecommendationDocument)
        assert doc.total_issues > 0, "Fallback doc must not be empty"
        assert doc.model_used == "claude-sonnet-4-6"
        for iss in doc.issues:
            assert iss.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


# ---------------------------------------------------------------------------
# Test 3: RecommendationDocument Pydantic schema validation
# ---------------------------------------------------------------------------

class TestRecommendationDocSchema:
    def test_valid_doc_passes(self):
        doc = _make_doc()
        assert doc.total_issues == 1
        assert doc.repo_name == "my-repo"

    def test_invalid_severity_raises(self):
        with pytest.raises(ValidationError):
            IssueDetail(
                id="ISS-001",
                title="Bad",
                severity="UNKNOWN",  # not in Literal
                affected_files=[],
                description="x",
                fix=[],
                effort="Low",
                priority=1,
            )

    def test_invalid_effort_raises(self):
        with pytest.raises(ValidationError):
            IssueDetail(
                id="ISS-002",
                title="Bad",
                severity="HIGH",
                affected_files=[],
                description="x",
                fix=[],
                effort="Extreme",  # not in Literal
                priority=1,
            )

    def test_total_issues_auto_computed(self):
        doc = _make_doc(total_issues=0)
        assert doc.total_issues == len(doc.issues)

    def test_severity_summary_auto_computed(self):
        doc = _make_doc(severity_summary={})
        assert "HIGH" in doc.severity_summary
        assert doc.severity_summary["HIGH"] == 1


# ---------------------------------------------------------------------------
# Test 4: HTML exporter contains issue ID
# ---------------------------------------------------------------------------

class TestHtmlExporterContainsIssueId:
    def test_html_exporter_contains_issue_id(self):
        doc = _make_doc()
        html = export_to_html(doc)
        assert "ISS-001" in html


# ---------------------------------------------------------------------------
# Test 5: HTML exporter severity badge colour
# ---------------------------------------------------------------------------

class TestHtmlExporterSeverityBadge:
    def test_html_exporter_severity_badge_critical(self):
        from datetime import date, timedelta

        today = date.today().isoformat()
        doc = RecommendationDocument(
            repo_name="test",
            analysis_date=today,
            model_used="claude-sonnet-4-6",
            health_score=40.0,
            issues=[
                IssueDetail(
                    id="ISS-001",
                    title="Critical problem",
                    severity="CRITICAL",
                    affected_files=["app.py:1"],
                    description="Very bad",
                    fix=["Fix it now"],
                    effort="High",
                    priority=1,
                )
            ],
            total_issues=1,
            next_review_date=(date.today() + timedelta(days=30)).isoformat(),
        )
        html = export_to_html(doc)
        # CRITICAL badge uses #dc2626 background
        assert "#dc2626" in html

    def test_html_exporter_high_badge_colour(self):
        doc = _make_doc()  # default severity is HIGH
        html = export_to_html(doc)
        assert "#ea580c" in html


# ---------------------------------------------------------------------------
# Test 6: HTML exporter is self-contained (no external resource URLs)
# ---------------------------------------------------------------------------

class TestHtmlExporterSelfContained:
    def test_html_exporter_self_contained(self):
        doc = _make_doc()
        html = export_to_html(doc)
        # No external stylesheet/script/image links
        assert 'src="http' not in html
        assert "cdn." not in html.lower()
        assert "fonts.googleapis" not in html
        assert "fonts.gstatic" not in html
        # Must be a complete HTML document
        assert "<!DOCTYPE html>" in html
        assert "<style>" in html
        assert "</html>" in html
