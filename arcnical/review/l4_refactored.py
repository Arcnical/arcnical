"""
L4 Review Agent - Provider Agnostic.

Uses abstract LLMProvider interface for vendor-neutral LLM access.
"""

from typing import Dict, Optional, List
import logging

from arcnical.schema import Recommendation, Severity, RecommendationCategory, Evidence, FileReference
from arcnical.report.builder import ReportBuilder
from .llm.base import LLMProvider, ReviewResult

logger = logging.getLogger(__name__)


class L4ReviewAgent:
    """
    L4 Review Agent using abstract LLM provider.

    Provider-agnostic code review agent that works with any LLM
    (Claude, OpenAI, Gemini, etc.).
    """

    def __init__(self, provider: LLMProvider):
        """
        Initialize L4 agent with a provider.

        Args:
            provider: LLMProvider instance (Claude, OpenAI, Gemini, etc.)

        Raises:
            ValueError: If provider is None
        """
        if provider is None:
            raise ValueError("LLMProvider is required")

        self.provider = provider
        self.report_builder = ReportBuilder()

        logger.info(
            f"L4ReviewAgent initialized with {provider.get_provider_name()} "
            f"({provider.get_model_name()})"
        )

    def review(self, repo_analysis):
        """
        Review repository analysis with LLM.

        Args:
            repo_analysis: Report from L1-L3 analysis

        Returns:
            Report with L4 findings added
        """
        try:
            logger.info(f"Starting L4 review with {self.provider.get_provider_name()}")

            # Extract context from report
            context = self._extract_context(repo_analysis)

            # Get LLM review using provider
            review_result = self.provider.review_code(
                code_snippet=context.get("code_sample", ""),
                context=context,
                metrics=context.get("metrics", {}),
            )

            logger.info(f"Received {len(review_result.findings)} findings from LLM")

            # Convert findings to recommendations
            l4_recommendations = self._convert_findings_to_recommendations(
                review_result.findings
            )

            # Add L4 recommendations to report
            if l4_recommendations:
                repo_analysis.recommendations.extend(l4_recommendations)
                repo_analysis.findings_count = len(repo_analysis.recommendations)

            logger.info(
                f"L4 review complete. Added {len(l4_recommendations)} recommendations. "
                f"Total: {repo_analysis.findings_count}"
            )

            return repo_analysis

        except Exception as e:
            logger.error(f"L4 review failed: {e}")
            raise

    def get_provider_name(self) -> str:
        """Get current provider name"""
        return self.provider.get_provider_name()

    def get_model_name(self) -> str:
        """Get current model name"""
        return self.provider.get_model_name()

    def health_check(self) -> bool:
        """Check if provider is healthy"""
        return self.provider.health_check()

    def _extract_context(self, report) -> Dict:
        """
        Extract review context from report.

        Args:
            report: Report from L1-L3 analysis

        Returns:
            Dict with context for LLM review
        """
        # Extract sample code or critical files
        code_sample = ""
        if hasattr(report, "summary") and hasattr(report.summary, "code_sample"):
            code_sample = report.summary.code_sample

        # Extract existing recommendations
        existing_findings = []
        if hasattr(report, "recommendations"):
            existing_findings = [r.model_dump() if hasattr(r, "model_dump") else r
                                for r in report.recommendations[:10]]

        # Extract metrics
        metrics = {}
        if hasattr(report, "metrics") and report.metrics:
            metrics = (
                report.metrics.model_dump()
                if hasattr(report.metrics, "model_dump")
                else report.metrics
            )

        return {
            "code_sample": code_sample,
            "findings": existing_findings,
            "metrics": metrics,
            "provider": self.provider.get_provider_name(),
            "model": self.provider.get_model_name(),
        }

    def _convert_findings_to_recommendations(self, findings: List[Dict]) -> List[Recommendation]:
        """
        Convert LLM findings to Recommendation objects.

        Args:
            findings: List of finding dicts from LLM

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        for i, finding in enumerate(findings, 1):
            try:
                # Map severity
                severity = self._map_severity(finding.get("severity", "medium"))

                # Create recommendation
                rec = Recommendation(
                    id=f"L4-{i:03d}",
                    title=finding.get("description", "L4 Finding"),
                    severity=severity,
                    category=RecommendationCategory.CODE_HEALTH,
                    layer="L4",
                    evidence=Evidence(
                        metric="LLM Review",
                        value=0.85,  # Confidence from LLM
                        references=[
                            FileReference(
                                file=finding.get("file", "unknown"),
                                line=finding.get("line_number", 0),
                                symbol=finding.get("symbol", ""),
                            )
                        ],
                    ),
                    rationale=finding.get("rationale", ""),
                    suggested_action=finding.get("suggested_action", ""),
                    verified=False,
                )

                recommendations.append(rec)

            except Exception as e:
                logger.warning(f"Failed to convert finding {i}: {e}")
                continue

        return recommendations

    @staticmethod
    def _map_severity(severity_str: str) -> Severity:
        """
        Map string severity to Severity enum.

        Args:
            severity_str: String severity level

        Returns:
            Severity enum value
        """
        severity_lower = severity_str.lower()

        if "critical" in severity_lower or "error" in severity_lower:
            return Severity.CRITICAL
        elif "high" in severity_lower:
            return Severity.HIGH
        elif "medium" in severity_lower or "warning" in severity_lower:
            return Severity.MEDIUM
        else:
            return Severity.LOW
