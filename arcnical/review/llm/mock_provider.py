"""
Mock LLM Provider for testing.

Provides deterministic responses without making real API calls.
"""

from typing import Dict, List
from .base import LLMProvider, ReviewResult


class MockLLMProvider(LLMProvider):
    """Mock provider for testing L4 agent without real API calls"""

    def __init__(self, deterministic: bool = True, findings_count: int = 3):
        """
        Initialize mock provider.

        Args:
            deterministic: Return same findings every time (default: True)
            findings_count: Number of findings to return (default: 3)
        """
        self.deterministic = deterministic
        self.findings_count = findings_count
        self.call_count = 0

    def review_code(self, code_snippet: str, context: Dict, metrics: Dict) -> ReviewResult:
        """
        Return mock review result.

        Args:
            code_snippet: (unused in mock)
            context: (unused in mock)
            metrics: (unused in mock)

        Returns:
            Mock ReviewResult with deterministic findings
        """
        self.call_count += 1

        # Generate findings
        findings = self._generate_findings()

        # Extract recommendations
        recommendations = [f["description"] for f in findings]

        return ReviewResult(
            findings=findings,
            recommendations=recommendations,
            confidence=0.9,
            provider="mock",
            model="mock-model",
            tokens_used=100 * len(findings),
            latency_seconds=0.1,
        )

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "mock"

    def get_model_name(self) -> str:
        """Return model name"""
        return "mock-model"

    def validate_config(self) -> bool:
        """Always valid for mock"""
        return True

    def health_check(self) -> bool:
        """Always healthy for mock"""
        return True

    def _generate_findings(self) -> List[Dict]:
        """Generate mock findings"""
        findings = []

        for i in range(self.findings_count):
            finding = {
                "id": f"MOCK-{i+1:03d}",
                "description": f"Mock finding {i+1}: This is a test finding",
                "severity": ["critical", "high", "medium"][i % 3],
                "category": ["architecture", "maintainability", "performance"][i % 3],
                "line_number": 10 + i,
                "file": "mock_file.py",
            }
            findings.append(finding)

        return findings

    def reset(self):
        """Reset call counter"""
        self.call_count = 0
