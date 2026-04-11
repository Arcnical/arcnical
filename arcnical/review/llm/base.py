"""
Abstract base classes for LLM providers.

Defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider API is unavailable"""
    pass


class ProviderConfigError(ProviderError):
    """Provider configuration is invalid"""
    pass


class ProviderTimeoutError(ProviderError):
    """Provider request timed out"""
    pass


@dataclass
class ReviewResult:
    """Standard output from LLM code review"""
    findings: List[Dict]
    recommendations: List[str]
    confidence: float
    provider: str
    model: str
    tokens_used: int
    latency_seconds: float


class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    @abstractmethod
    def review_code(
        self,
        code_snippet: str,
        context: Dict,
        metrics: Dict
    ) -> ReviewResult:
        """
        Review code and return findings.

        Args:
            code_snippet: Code to review
            context: Analysis context (findings, recommendations, etc.)
            metrics: Code metrics (complexity, instability, etc.)

        Returns:
            ReviewResult with findings and recommendations

        Raises:
            ProviderError: If review fails
            ProviderUnavailableError: If provider is unavailable
            ProviderTimeoutError: If request times out
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name (claude, openai, gemini)"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return model name being used"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if config is valid, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is accessible.

        Returns:
            True if provider is accessible, False otherwise
        """
        pass
