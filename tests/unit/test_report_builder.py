"""
Unit tests for Report Builder
"""

import pytest
from arcnical.report.builder import ReportBuilder, HealthScoreCalculator
from arcnical.schema import (
    Qualification, TargetClassification, Severity, PracticeDetection,
    DocsInfo, TestsInfo
)


class TestHealthScoreCalculator:
    """Tests for health score calculation"""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthScoreCalculator()
    
    def test_perfect_score_no_findings(self, calculator):
        """Test perfect score with no findings"""
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {
            "complexity_avg": 5,
            "instability_avg": 0.4
        }
        
        score = calculator.calculate_health_score(findings, metrics)
        
        assert score.overall >= 90  # Should be high
        assert score.structure >= 90
        assert score.maintainability >= 90
    
    def test_score_reduces_with_high_findings(self, calculator):
        """Test score reduces with high severity findings"""
        from arcnical.heuristics.l2_detector import L2Finding
        from arcnical.schema import RecommendationCategory
        
        finding = L2Finding(
            id="L2-001",
            title="Test finding",
            severity=Severity.CRITICAL,
            evidence_data={"test": "data"},
            category=RecommendationCategory.ARCHITECTURE
        )
        
        findings = {
            "l2_findings": [finding],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {
            "complexity_avg": 5,
            "instability_avg": 0.4
        }
        
        score = calculator.calculate_health_score(findings, metrics)
        
        assert score.overall < 90  # Should be reduced
    
    def test_security_findings_weighted_higher(self, calculator):
        """Test that security findings have higher weight"""
        from arcnical.heuristics.security_scanner import SecurityFinding
        
        security_finding = SecurityFinding(
            id="SEC-001",
            title="API key found",
            severity=Severity.CRITICAL,
            finding_type="API_KEY",
            description="test"
        )
        
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": [security_finding]
        }
        metrics = {}
        
        score = calculator.calculate_health_score(findings, metrics)
        
        # Security CRITICAL should heavily reduce score
        assert score.security < 50
    
    def test_score_clamped_to_0_100(self, calculator):
        """Test score is clamped between 0-100"""
        # Create massive findings list
        from arcnical.heuristics.l2_detector import L2Finding
        from arcnical.schema import RecommendationCategory
        
        findings_list = [
            L2Finding(
                id=f"L2-{i:03d}",
                title=f"Finding {i}",
                severity=Severity.CRITICAL,
                evidence_data={},
                category=RecommendationCategory.ARCHITECTURE
            )
            for i in range(20)
        ]
        
        findings = {
            "l2_findings": findings_list,
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {}
        
        score = calculator.calculate_health_score(findings, metrics)
        
        assert 0 <= score.overall <= 100
        assert 0 <= score.structure <= 100
        assert 0 <= score.maintainability <= 100


class TestReportBuilder:
    """Tests for report building"""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return ReportBuilder()
    
    @pytest.fixture
    def basic_qualification(self):
        """Create basic qualification"""
        return Qualification(
            classification=TargetClassification.APPLICATION,
            confidence=0.95,
            signals=["has_main", "has_tests"]
        )
    
    @pytest.fixture
    def basic_practice(self):
        """Create basic practice detection"""
        return PracticeDetection(
            architecture_style="layered",
            api_surfaces=["rest"],
            ci_cd=["github_actions"],
            containerization=["docker"],
            iac=[],
            observability=["sentry"],
            docs=DocsInfo(readme=True),
            tests=TestsInfo(framework="pytest", ratio=0.2)
        )
    
    def test_build_report_complete(self, builder, basic_qualification, basic_practice):
        """Test building a complete report"""
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {
            "complexity_avg": 8,
            "instability_avg": 0.6,
            "circular_dependencies": 0,
            "god_classes": 0,
            "file_count": 50,
            "loc_total": 5000
        }
        
        report = builder.build_report(
            qualification=basic_qualification,
            findings=findings,
            metrics=metrics,
            practice=basic_practice,
            repo_path=".",
            repo_name="test-repo"
        )
        
        assert report.metadata is not None
        assert report.qualification == basic_qualification
        assert report.summary is not None
        assert report.scores is not None
        assert report.recommendations is not None
    
    def test_report_has_metadata(self, builder, basic_qualification, basic_practice):
        """Test report includes all metadata"""
        findings = {
            "l2_findings": [],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {}
        
        report = builder.build_report(
            qualification=basic_qualification,
            findings=findings,
            metrics=metrics,
            practice=basic_practice,
            repo_path=".",
            repo_name="test-repo",
            commit_sha="abc123"
        )
        
        assert report.metadata.tool_version == "0.2.0"
        assert report.metadata.commit_sha == "abc123"
        assert report.metadata.generated_at is not None
    
    def test_report_aggregates_recommendations(self, builder, basic_qualification, basic_practice):
        """Test report aggregates all recommendations"""
        from arcnical.heuristics.l2_detector import L2Finding
        from arcnical.schema import RecommendationCategory
        
        finding = L2Finding(
            id="L2-001",
            title="Test finding",
            severity=Severity.HIGH,
            evidence_data={"test": "data"},
            category=RecommendationCategory.ARCHITECTURE
        )
        
        findings = {
            "l2_findings": [finding],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {}
        
        report = builder.build_report(
            qualification=basic_qualification,
            findings=findings,
            metrics=metrics,
            practice=basic_practice,
            repo_path=".",
            repo_name="test-repo"
        )
        
        assert len(report.recommendations) >= 1
    
    def test_report_ranked_by_severity(self, builder, basic_qualification, basic_practice):
        """Test recommendations are ranked by severity"""
        from arcnical.heuristics.l2_detector import L2Finding
        from arcnical.schema import RecommendationCategory
        
        low_finding = L2Finding(
            id="L2-001",
            title="Low severity",
            severity=Severity.LOW,
            evidence_data={},
            category=RecommendationCategory.ARCHITECTURE
        )
        
        high_finding = L2Finding(
            id="L2-002",
            title="High severity",
            severity=Severity.HIGH,
            evidence_data={},
            category=RecommendationCategory.ARCHITECTURE
        )
        
        findings = {
            "l2_findings": [low_finding, high_finding],
            "l3_findings": [],
            "security_findings": []
        }
        metrics = {}
        
        report = builder.build_report(
            qualification=basic_qualification,
            findings=findings,
            metrics=metrics,
            practice=basic_practice,
            repo_path=".",
            repo_name="test-repo"
        )
        
        # High severity should come first
        if len(report.recommendations) >= 2:
            assert report.recommendations[0].severity == Severity.HIGH
            assert report.recommendations[1].severity == Severity.LOW
