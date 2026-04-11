"""
Claude API provider implementation.

Implements LLMProvider interface using Anthropic's Claude API.
"""

import time
from typing import Dict, List, Optional
from anthropic import Anthropic, APIError, APIConnectionError, APITimeoutError

from .base import (
    LLMProvider,
    ReviewResult,
    ProviderError,
    ProviderUnavailableError,
    ProviderConfigError,
    ProviderTimeoutError,
)


class ClaudeProvider(LLMProvider):
    """Claude API implementation of LLMProvider"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0,
        max_tokens: int = 4000,
        timeout: int = 30,
    ):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-sonnet-4-6)
            temperature: Sampling temperature (default: 0)
            max_tokens: Max tokens in response (default: 4000)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            ProviderConfigError: If API key is missing or invalid
        """
        if not api_key:
            raise ProviderConfigError("Claude API key is required")

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        try:
            self.client = Anthropic(api_key=api_key)
        except Exception as e:
            raise ProviderConfigError(f"Failed to initialize Claude client: {e}")

    def review_code(self, code_snippet: str, context: Dict, metrics: Dict) -> ReviewResult:
        """
        Review code using Claude API.

        Args:
            code_snippet: Code to review
            context: Analysis context
            metrics: Code metrics

        Returns:
            ReviewResult with Claude's analysis

        Raises:
            ProviderUnavailableError: If Claude API is unavailable
            ProviderTimeoutError: If request times out
            ProviderError: If review fails
        """
        try:
            start_time = time.time()

            # Build prompt from code, context, metrics
            prompt = self._build_prompt(code_snippet, context, metrics)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
            )

            latency = time.time() - start_time

            # Extract response text
            response_text = response.content[0].text

            # Parse findings from response
            findings = self._parse_findings(response_text)

            # Extract recommendations
            recommendations = self._extract_recommendations(findings)

            return ReviewResult(
                findings=findings,
                recommendations=recommendations,
                confidence=0.85,  # Claude's typical confidence
                provider="claude",
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                latency_seconds=latency,
            )

        except APITimeoutError as e:
            raise ProviderTimeoutError(f"Claude API request timed out: {e}")
        except APIConnectionError as e:
            raise ProviderUnavailableError(f"Claude API unavailable: {e}")
        except APIError as e:
            raise ProviderError(f"Claude API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error during Claude review: {e}")

    def validate_config(self) -> bool:
        """
        Validate Claude configuration.

        Returns:
            True if config is valid, False otherwise
        """
        try:
            # Make minimal API call to validate
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
                timeout=self.timeout,
            )
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        """
        Check if Claude API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        return self.validate_config()

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "claude"

    def get_model_name(self) -> str:
        """Return model name"""
        return self.model

    def _build_prompt(self, code: str, context: Dict, metrics: Dict) -> str:
        """
        Build review prompt for Claude.

        Args:
            code: Code to review
            context: Analysis context
            metrics: Code metrics

        Returns:
            Prompt string for Claude
        """
        prompt = f"""Review this code for architecture quality and maintainability:

{code}

Context:
- Metrics: {metrics}
- Current findings: {len(context.get('findings', []))} issues detected

Provide specific, actionable recommendations."""

        return prompt

    def _parse_findings(self, response: str) -> List[Dict]:
        """
        Parse Claude's response into findings.

        Args:
            response: Claude's response text

        Returns:
            List of finding dictionaries
        """
        # Simple parsing: split by lines and extract key points
        findings = []
        lines = response.split("\n")

        for i, line in enumerate(lines):
            if line.strip().startswith("-") or line.strip().startswith("•"):
                finding = {
                    "description": line.strip()[2:],  # Remove bullet point
                    "severity": self._extract_severity(line),
                    "line_number": i,
                }
                findings.append(finding)

        return findings

    def _extract_recommendations(self, findings: List[Dict]) -> List[str]:
        """
        Extract recommendations from findings.

        Args:
            findings: List of findings

        Returns:
            List of recommendation strings
        """
        recommendations = []

        for finding in findings:
            if "description" in finding:
                recommendations.append(finding["description"])

        return recommendations[:10]  # Return top 10

    def _extract_severity(self, text: str) -> str:
        """
        Extract severity from finding text.

        Args:
            text: Finding text

        Returns:
            Severity level (critical, high, medium, low)
        """
        text_lower = text.lower()

        if "critical" in text_lower or "error" in text_lower:
            return "critical"
        elif "high" in text_lower or "serious" in text_lower:
            return "high"
        elif "medium" in text_lower or "warning" in text_lower:
            return "medium"
        else:
            return "low"
