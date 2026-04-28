"""
Report Builder - Orchestrates report creation

Transforms qualification, findings, metrics into a complete Report object
ready for rendering as Markdown or JSON.
"""

from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import json

from arcnical.schema import (
    Report, Metadata, Qualification, Summary, LayerResult, 
    ArchitectureHealthScore, Metrics, PracticeDetection, 
    Recommendation, SecurityFinding, LayerStatus, Severity
)
from arcnical.graph.builder import CodeKnowledgeGraph


class HealthScoreCalculator:
    """Calculates architecture health scores (0-100)"""
    
    @staticmethod
    def calculate_health_score(
        findings: Dict[str, List],
        metrics: Dict
    ) -> ArchitectureHealthScore:
        """
        Calculate overall architecture health score.
        
        Scoring formula (0-100):
        - Start with 100
        - Deduct for findings (severity-weighted)
        - Factor in metrics (complexity, coupling, instability)
        - Return structured score breakdown
        
        Args:
            findings: Dict with l2_findings, l3_findings, security_findings
            metrics: Dict with complexity, coupling, etc.
            
        Returns:
            ArchitectureHealthScore with overall + breakdown scores
        """
        l2_findings = findings.get("l2_findings", [])
        l3_findings = findings.get("l3_findings", [])
        security_findings = findings.get("security_findings", [])

        severity_weight = {
            Severity.CRITICAL: 15,
            Severity.HIGH: 10,
            Severity.MEDIUM: 5,
            Severity.LOW: 2,
        }
        sec_weight = {
            Severity.CRITICAL: 60,
            Severity.HIGH: 30,
            Severity.MEDIUM: 15,
            Severity.LOW: 5,
        }

        # Deductions capped per group so many low-severity findings can't floor the score
        l2_deduction  = min(35, sum(severity_weight.get(f.severity, 5) for f in l2_findings))
        l3_deduction  = min(25, sum(severity_weight.get(f.severity, 5) for f in l3_findings))
        sec_deduction = min(40, sum(sec_weight.get(f.severity, 15) for f in security_findings))

        complexity_avg   = metrics.get("complexity_avg", 0)
        instability_avg  = metrics.get("instability_avg", 0)
        metrics_deduction = 0.0
        if complexity_avg > 15:
            metrics_deduction += min(10, (complexity_avg - 15) / 2)
        if instability_avg > 0.8:
            metrics_deduction += min(10, (instability_avg - 0.8) * 50)

        def _clamp(v: float) -> float:
            return max(0.0, min(100.0, v))

        overall_score  = _clamp(100.0 - l2_deduction - l3_deduction - sec_deduction - metrics_deduction)
        maintainability = _clamp(100.0 - l3_deduction - metrics_deduction)
        complexity_score = _clamp(100.0 - l2_deduction - metrics_deduction)
        security_score   = _clamp(100.0 - sec_deduction)

        return ArchitectureHealthScore(
            overall=round(overall_score, 1),
            maintainability=round(maintainability, 1),
            structure=round(complexity_score, 1),
            security=round(security_score, 1),
        )


class ReportBuilder:
    """Builds complete Report objects from analysis results"""
    
    def __init__(self):
        """Initialize report builder"""
        self.health_calculator = HealthScoreCalculator()
    
    def build_report(
        self,
        qualification: Qualification,
        findings: Dict[str, List],
        metrics: Dict,
        practice: PracticeDetection,
        repo_path: str,
        repo_name: str = "Repository",
        commit_sha: Optional[str] = None,
        graph_hash: Optional[str] = None
    ) -> Report:
        """
        Build complete Report object.
        
        Args:
            qualification: Target qualification (app/library/etc)
            findings: Dict with l2_findings, l3_findings, security_findings
            metrics: Dict with complexity, coupling, metrics
            practice: PracticeDetection summary
            repo_path: Repository root path
            repo_name: Name of repository
            commit_sha: Git commit SHA (optional)
            graph_hash: Knowledge graph hash (optional)
            
        Returns:
            Complete Report object ready for rendering
        """
        
        # Build metadata
        metadata = self._build_metadata(
            repo_name=repo_name,
            commit_sha=commit_sha,
            graph_hash=graph_hash or self._calculate_hash({})
        )
        
        # Build summary
        summary = self._build_summary(
            repo_name=repo_name,
            metrics=metrics
        )
        
        # Build layer results
        layer_results = self._build_layer_results(findings)
        
        # Calculate health score
        health_score = self.health_calculator.calculate_health_score(
            findings=findings,
            metrics=metrics
        )
        
        # Get all recommendations (convert findings to recommendations)
        recommendations = self._aggregate_recommendations(findings)
        
        # Build report
        report = Report(
            metadata=metadata,
            target_type=qualification.classification,
            qualification=qualification,
            summary=summary,
            layers=layer_results,
            scores=health_score,
            metrics=self._build_metrics_summary(metrics),
            practice_detection=practice,
            recommendations=recommendations,
        )
        
        return report
    
    def _build_metadata(
        self,
        repo_name: str,
        commit_sha: Optional[str],
        graph_hash: str
    ) -> Metadata:
        """Build metadata section"""
        return Metadata(
            tool_version="0.2.0",
            model="claude-sonnet-4-6",
            prompt_version="v1",
            layer_config_version="v1",
            graph_hash=graph_hash,
            commit_sha=commit_sha or "unknown",
            generated_at=datetime.utcnow()
        )
    
    def _build_summary(
        self,
        repo_name: str,
        metrics: Dict
    ) -> Summary:
        """Build summary section"""
        return Summary(
            repo=repo_name,
            language_breakdown=metrics.get("language_breakdown", {}),
            loc_total=metrics.get("loc_total", 0),
            file_count=metrics.get("file_count", 0)
        )
    
    def _build_layer_results(self, findings: Dict) -> List[LayerResult]:
        """Build layer result status"""
        l2_count = len(findings.get("l2_findings", []))
        l3_count = len(findings.get("l3_findings", []))
        security_count = len(findings.get("security_findings", []))
        
        return [
            LayerResult(
                id="L1",
                name="Qualification",
                status=LayerStatus.PASSED,
                findings_count=0,
                blocking_findings=[]
            ),
            LayerResult(
                id="L2",
                name="Structural Issues",
                status=LayerStatus.WARNED if l2_count > 0 else LayerStatus.PASSED,
                findings_count=l2_count,
                blocking_findings=self._get_high_severity_titles(
                    findings.get("l2_findings", [])
                )
            ),
            LayerResult(
                id="L3",
                name="Code Quality",
                status=LayerStatus.WARNED if l3_count > 0 else LayerStatus.PASSED,
                findings_count=l3_count,
                blocking_findings=self._get_high_severity_titles(
                    findings.get("l3_findings", [])
                )
            ),
            LayerResult(
                id="L4",
                name="LLM Review",
                status=LayerStatus.PENDING,
                findings_count=0,
                blocking_findings=[]
            )
        ]
    
    def _build_metrics_summary(self, metrics: Dict) -> Metrics:
        """Build metrics summary"""
        return Metrics(
            complexity_avg=metrics.get("complexity_avg", 0),
            complexity_p95=metrics.get("complexity_p95", 0),
            instability_avg=metrics.get("instability_avg", 0),
            circular_dependency_count=metrics.get("circular_dependencies", 0),
            god_class_count=metrics.get("god_classes", 0),
            hotspot_files=metrics.get("hotspot_files", [])
        )
    
    def _aggregate_recommendations(self, findings: Dict) -> List[Recommendation]:
        """Convert all findings to recommendations"""
        recommendations = []
        
        # Convert L2 findings
        for finding in findings.get("l2_findings", []):
            if hasattr(finding, 'to_recommendation'):
                recommendations.append(finding.to_recommendation())
        
        # Convert L3 findings
        for finding in findings.get("l3_findings", []):
            if hasattr(finding, 'to_recommendation'):
                recommendations.append(finding.to_recommendation())
        
        # Convert Security findings
        for finding in findings.get("security_findings", []):
            if hasattr(finding, 'to_recommendation'):
                recommendations.append(finding.to_recommendation())
        
        # Sort by severity (CRITICAL > HIGH > MEDIUM > LOW)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3
        }
        
        recommendations.sort(
            key=lambda r: severity_order.get(r.severity, 999)
        )
        
        return recommendations
    
    def _find_blocking_findings(self, recommendations: List[Recommendation]) -> List[str]:
        """Find blocking findings (L2 with HIGH severity)"""
        blocking = []
        for rec in recommendations:
            if rec.layer == "L2" and rec.severity == Severity.HIGH:
                blocking.append(rec.title)
        return blocking[:5]  # Return top 5
    
    def _get_high_severity_titles(self, findings: List) -> List[str]:
        """Return titles of high/critical severity findings"""
        titles = []
        for finding in findings:
            if hasattr(finding, 'severity') and finding.severity in (Severity.CRITICAL, Severity.HIGH):
                titles.append(getattr(finding, 'title', str(finding)))
        return titles
    
    @staticmethod
    def _calculate_hash(data: Dict) -> str:
        """Calculate SHA256 hash of data"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
