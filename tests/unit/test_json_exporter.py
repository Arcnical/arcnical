# tests/unit/test_json_exporter.py
"""Tests for JSON exporter functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from arcnical.cli.json_exporter import AnalysisExporter
from arcnical.schema import (
    Report, Recommendation, Evidence, FileReference, Severity,
    RecommendationCategory, ArchitectureHealthScore, Metadata, TokenUsage,
    PracticeDetection, TestsInfo, DocsInfo, Qualification,
    TargetClassification, Summary, Metrics, LayerResult, LayerStatus,
)


class TestAnalysisExporter:
    """Test suite for AnalysisExporter."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def exporter(self, temp_dir):
        """Create exporter instance with temp directory."""
        return AnalysisExporter(output_dir=temp_dir)

    @pytest.fixture
    def sample_report(self):
        """Create a sample report for testing."""
        metadata = Metadata(
            tool_version="0.2.0",
            model="claude-sonnet-4-6",
            prompt_version="1.0",
            layer_config_version="1.0",
            graph_hash="abc123",
            commit_sha="def456",
            generated_at=datetime(2024, 4, 11, 14, 30, 0),
            depth="standard",
            force_used=False,
            token_usage=TokenUsage(),
        )

        scores = ArchitectureHealthScore(
            overall=85,
            maintainability=80,
            structure=90,
            security=75,
        )

        # Create sample finding
        evidence = Evidence(
            metric="complexity",
            value=18.5,
            references=[
                FileReference(file="src/main.py", line=42, symbol="main_function")
            ]
        )

        finding = Recommendation(
            id="L2-001",
            title="High complexity function",
            severity=Severity.HIGH,
            category=RecommendationCategory.MAINTAINABILITY,
            layer="L2",
            evidence=evidence,
            rationale="Function exceeds complexity threshold",
            suggested_action="Refactor function into smaller pieces",
            verified=True,
            line=42,
        )

        practice = PracticeDetection(
            architecture_style="layered",
            api_surfaces=["rest"],
            ci_cd=["github_actions"],
            containerization=["docker"],
            iac=[],
            observability=[],
            docs=DocsInfo(readme=True),
            tests=TestsInfo(framework="pytest", ratio=0.5),
        )

        qualification = Qualification(
            classification=TargetClassification.APPLICATION,
            confidence=0.95,
            signals=["has_main", "has_tests"],
        )

        summary = Summary(
            repo="test-repo",
            language_breakdown={},
            loc_total=500,
            file_count=10,
        )

        metrics = Metrics(
            complexity_avg=8.0,
            complexity_p95=15.0,
            instability_avg=0.4,
            circular_dependency_count=0,
            god_class_count=0,
            hotspot_files=[],
        )

        layers = [
            LayerResult(id="L1", name="Qualification", status=LayerStatus.PASSED,
                        findings_count=0, blocking_findings=[]),
            LayerResult(id="L2", name="Structural Issues", status=LayerStatus.WARNED,
                        findings_count=1, blocking_findings=["High complexity function"]),
        ]

        report = Report(
            metadata=metadata,
            target_type=TargetClassification.APPLICATION,
            qualification=qualification,
            summary=summary,
            layers=layers,
            scores=scores,
            metrics=metrics,
            practice_detection=practice,
            recommendations=[finding],
        )

        return report

    def test_export_creates_file(self, exporter, sample_report):
        """Test that export creates a JSON file."""
        filepath = exporter.export(sample_report)
        
        assert filepath.exists()
        assert filepath.suffix == ".json"

    def test_export_contains_valid_json(self, exporter, sample_report):
        """Test that exported file contains valid JSON."""
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
        assert "metadata" in data
        assert "scores" in data
        assert "findings" in data

    def test_export_includes_metadata(self, exporter, sample_report):
        """Test that metadata is included in export."""
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        metadata = data["metadata"]
        assert metadata["tool_version"] == "0.2.0"
        assert metadata["model"] == "claude-sonnet-4-6"
        assert metadata["depth"] == "standard"

    def test_export_includes_health_scores(self, exporter, sample_report):
        """Test that health scores are included."""
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        scores = data["scores"]
        assert scores["overall"] == 85
        assert scores["maintainability"] == 80
        assert scores["structure"] == 90
        assert scores["security"] == 75

    def test_export_includes_findings(self, exporter, sample_report):
        """Test that findings are included."""
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        findings = data["findings"]
        assert len(findings) > 0
        assert findings[0]["id"] == "L2-001"
        assert findings[0]["severity"] == "High"

    def test_export_includes_evidence(self, exporter, sample_report):
        """Test that evidence is properly formatted."""
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        evidence = data["findings"][0]["evidence"]
        assert evidence["metric"] == "complexity"
        assert evidence["value"] == 18.5
        assert len(evidence["references"]) > 0
        assert evidence["references"][0]["file"] == "src/main.py"
        assert evidence["references"][0]["line"] == 42

    def test_export_includes_practice_detection(self, exporter, sample_report):
        """Test that practice detection is included."""
        filepath = exporter.export(sample_report)

        with open(filepath, 'r') as f:
            data = json.load(f)

        practice = data["practice_detection"]
        assert practice["has_tests"]["detected"] is True
        assert practice["has_documentation"]["detected"] is True
        assert practice["has_ci_cd"]["detected"] is True
        assert practice["code_coverage"]["percentage"] is None

    def test_export_custom_filename(self, exporter, sample_report):
        """Test export with custom filename."""
        filepath = exporter.export(sample_report, filename="custom_analysis.json")
        
        assert filepath.name == "custom_analysis.json"
        assert filepath.exists()

    def test_export_invalid_report_raises_error(self, exporter):
        """Test that invalid report raises ValueError."""
        with pytest.raises(ValueError):
            exporter.export("not a report")

    def test_load_json(self, exporter, sample_report):
        """Test loading JSON file."""
        filepath = exporter.export(sample_report)
        loaded = AnalysisExporter.load_json(str(filepath))
        
        assert isinstance(loaded, dict)
        assert "metadata" in loaded
        assert loaded["metadata"]["tool_version"] == "0.2.0"

    def test_load_json_invalid_file_raises_error(self, exporter):
        """Test that loading invalid file raises error."""
        with pytest.raises(FileNotFoundError):
            AnalysisExporter.load_json("nonexistent.json")

    def test_get_latest_analysis_no_file(self):
        """Test get_latest_analysis when no file exists."""
        # This test assumes .arcnical/results doesn't exist or is empty
        result = AnalysisExporter.get_latest_analysis()
        # Result can be None if file doesn't exist
        assert result is None or isinstance(result, dict)

    def test_export_creates_directory(self):
        """Test that export creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = str(Path(tmpdir) / "subdir" / "results")
            exporter = AnalysisExporter(output_dir=output_dir)
            
            assert Path(output_dir).exists()

    def test_export_multiple_findings(self, exporter, sample_report):
        """Test export with multiple findings."""
        # Add more findings to sample report
        sample_report.recommendations.append(
            Recommendation(
                id="L2-002",
                title="Another finding",
                severity=Severity.MEDIUM,
                category=RecommendationCategory.STRUCTURE,
                layer="L2",
                evidence=Evidence(
                    metric="lines_of_code",
                    value=250,
                    references=[FileReference(file="src/utils.py", line=1, symbol="module")]
                ),
                rationale="File is too large",
                suggested_action="Split into smaller modules",
                verified=True,
                line=1,
            )
        )
        
        filepath = exporter.export(sample_report)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert len(data["findings"]) == 2
        assert data["findings"][1]["id"] == "L2-002"

    def test_export_json_is_indented(self, exporter, sample_report):
        """Test that exported JSON is human-readable (indented)."""
        filepath = exporter.export(sample_report)
        
        content = filepath.read_text()
        # Check if content has indentation (multiple spaces at line start)
        assert "  " in content

    def test_export_includes_blocking_findings(self, exporter, sample_report):
        """Test that blocking findings are included."""
        filepath = exporter.export(sample_report)

        with open(filepath, 'r') as f:
            data = json.load(f)

        assert "blocking_findings" in data
        # HIGH severity finding L2-001 should appear as blocking
        assert "L2-001" in data["blocking_findings"]

    def test_export_includes_file_structure(self, exporter, sample_report):
        """Test that file structure is included."""
        filepath = exporter.export(sample_report)

        with open(filepath, 'r') as f:
            data = json.load(f)

        file_struct = data["file_structure"]
        assert "total_files" in file_struct
        assert "files" in file_struct
        assert file_struct["total_files"] >= 1
