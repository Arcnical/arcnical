"""
Unit tests for Report Formatters
"""

import pytest
import json
from arcnical.report.formatters import MarkdownFormatter, JSONFormatter
from arcnical.report.builder import ReportBuilder
from arcnical.schema import (
    Qualification, TargetClassification, PracticeDetection, Severity,
    DocsInfo, TestsInfo
)


class TestMarkdownFormatter:
    """Tests for Markdown formatting"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return MarkdownFormatter()
    
    @pytest.fixture
    def sample_report(self):
        """Create sample report for testing"""
        builder = ReportBuilder()
        qualification = Qualification(
            classification=TargetClassification.APPLICATION,
            confidence=0.95,
            signals=[]
        )
        practice = PracticeDetection(
            architecture_style="layered",
            api_surfaces=[],
            ci_cd=[],
            containerization=[],
            iac=[],
            observability=[],
            docs=DocsInfo(),
            tests=TestsInfo()
        )
        
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {
            "complexity_avg": 8,
            "instability_avg": 0.6,
            "circular_dependencies": 0,
            "god_classes": 0
        }
        
        return builder.build_report(
            qualification=qualification,
            findings=findings,
            metrics=metrics,
            practice=practice,
            repo_path=".",
            repo_name="test-repo"
        )
    
    def test_format_report_produces_string(self, formatter, sample_report):
        """Test that formatting produces a string"""
        result = formatter.format_report(sample_report)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_markdown_includes_header(self, formatter, sample_report):
        """Test Markdown includes main header"""
        result = formatter.format_report(sample_report)
        
        assert "# Arcnical Architecture Review Report" in result
    
    def test_markdown_includes_health_score(self, formatter, sample_report):
        """Test Markdown includes health score section"""
        result = formatter.format_report(sample_report)
        
        assert "## Architecture Health Score" in result
        assert "Overall:" in result
    
    def test_markdown_includes_metrics(self, formatter, sample_report):
        """Test Markdown includes metrics section"""
        result = formatter.format_report(sample_report)
        
        assert "## Metrics" in result or "Average Complexity" in result
    
    def test_markdown_includes_severity_emojis(self, formatter, sample_report):
        """Test Markdown uses severity emojis"""
        result = formatter.format_report(sample_report)
        
        # Check for severity indicators
        assert "🟢" in result or "🟠" in result or "🟡" in result or "🔴" in result
    
    def test_markdown_is_valid_structure(self, formatter, sample_report):
        """Test Markdown has valid structure"""
        result = formatter.format_report(sample_report)
        
        # Check for basic Markdown structure
        assert "\n" in result
        assert "##" in result  # Has headers


class TestJSONFormatter:
    """Tests for JSON formatting"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return JSONFormatter()
    
    @pytest.fixture
    def sample_report(self):
        """Create sample report for testing"""
        builder = ReportBuilder()
        qualification = Qualification(
            classification=TargetClassification.APPLICATION,
            confidence=0.95,
            signals=[]
        )
        practice = PracticeDetection(
            architecture_style="layered",
            api_surfaces=[],
            ci_cd=[],
            containerization=[],
            iac=[],
            observability=[],
            docs=DocsInfo(),
            tests=TestsInfo()
        )
        
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {}
        
        return builder.build_report(
            qualification=qualification,
            findings=findings,
            metrics=metrics,
            practice=practice,
            repo_path=".",
            repo_name="test-repo"
        )
    
    def test_format_report_produces_string(self, formatter, sample_report):
        """Test that formatting produces a string"""
        result = formatter.format_report(sample_report)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_json_is_valid(self, formatter, sample_report):
        """Test that output is valid JSON"""
        result = formatter.format_report(sample_report)
        
        # Should be parseable as JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
    
    def test_json_includes_metadata(self, formatter, sample_report):
        """Test JSON includes metadata"""
        result = formatter.format_report(sample_report)
        parsed = json.loads(result)
        
        assert "metadata" in parsed
        assert "tool_version" in parsed["metadata"]
    
    def test_json_includes_recommendations(self, formatter, sample_report):
        """Test JSON includes recommendations"""
        result = formatter.format_report(sample_report)
        parsed = json.loads(result)
        
        assert "recommendations" in parsed or "findings_count" in parsed
    
    def test_json_compact_format(self, formatter, sample_report):
        """Test compact JSON format"""
        result = formatter.format_report_compact(sample_report)
        
        assert isinstance(result, str)
        # Compact should be on one line (no newlines except possibly at end)
        assert "\n" not in result.strip()
        
        # Should still be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
    
    def test_json_matches_schema(self, formatter, sample_report):
        """Test JSON matches Report schema"""
        result = formatter.format_report(sample_report)
        parsed = json.loads(result)
        
        # Check key fields exist
        required_fields = [
            "metadata",
            "qualification",
            "summary",
            "scores"
        ]
        
        for field in required_fields:
            assert field in parsed, f"Missing field: {field}"
