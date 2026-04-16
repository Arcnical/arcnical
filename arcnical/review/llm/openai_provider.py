"""
OpenAI provider implementation.

Implements LLMProvider interface using OpenAI's Chat Completions API.
"""

import time
from typing import Dict, List

from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from .base import (
    LLMProvider,
    ReviewResult,
    ProviderError,
    ProviderUnavailableError,
    ProviderConfigError,
    ProviderTimeoutError,
)


class OpenAIProvider(LLMProvider):
    """OpenAI API implementation of LLMProvider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0,
        max_tokens: int = 4000,
        timeout: int = 30,
        **kwargs,
    ):
        if not api_key:
            raise ProviderConfigError("OpenAI API key is required")

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        try:
            self.client = OpenAI(api_key=api_key, timeout=timeout)
        except Exception as e:
            raise ProviderConfigError(f"Failed to initialize OpenAI client: {e}")

    def review_code(self, code_snippet: str, context: Dict, metrics: Dict) -> ReviewResult:
        """
        Review code using OpenAI Chat Completions API.

        Raises:
            ProviderUnavailableError: If OpenAI API is unreachable.
            ProviderTimeoutError: If the request times out.
            ProviderError: For all other API errors.
        """
        try:
            start_time = time.time()

            prompt = self._build_prompt(code_snippet, context, metrics)

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            latency = time.time() - start_time

            response_text = response.choices[0].message.content or ""

            findings = self._parse_findings(response_text)
            recommendations = self._extract_recommendations(findings)

            tokens_used = 0
            if response.usage:
                tokens_used = response.usage.prompt_tokens + response.usage.completion_tokens

            return ReviewResult(
                findings=findings,
                recommendations=recommendations,
                confidence=0.85,
                provider="openai",
                model=self.model,
                tokens_used=tokens_used,
                latency_seconds=latency,
            )

        except APITimeoutError as e:
            raise ProviderTimeoutError(f"OpenAI request timed out: {e}")
        except APIConnectionError as e:
            raise ProviderUnavailableError(f"OpenAI API unavailable: {e}")
        except APIError as e:
            raise ProviderError(f"OpenAI API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error during OpenAI review: {e}")

    def validate_config(self) -> bool:
        """Make a minimal API call to confirm the key and model are valid."""
        try:
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        return self.validate_config()

    def get_provider_name(self) -> str:
        return "openai"

    def get_model_name(self) -> str:
        return self.model

    def _build_prompt(self, code: str, context: Dict, metrics: Dict) -> str:
        return f"""Review this code for architecture quality and maintainability:

{code}

Context:
- Metrics: {metrics}
- Current findings: {len(context.get('findings', []))} issues detected

Provide specific, actionable recommendations."""

    def _parse_findings(self, response: str) -> List[Dict]:
        findings = []
        for i, line in enumerate(response.split("\n")):
            if line.strip().startswith(("-", "•")):
                findings.append({
                    "description": line.strip()[2:],
                    "severity": self._extract_severity(line),
                    "line_number": i,
                })
        return findings

    def _extract_recommendations(self, findings: List[Dict]) -> List[str]:
        return [f["description"] for f in findings if "description" in f][:10]

    def _extract_severity(self, text: str) -> str:
        t = text.lower()
        if "critical" in t or "error" in t:
            return "critical"
        elif "high" in t or "serious" in t:
            return "high"
        elif "medium" in t or "warning" in t:
            return "medium"
        return "low"
