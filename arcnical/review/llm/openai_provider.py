"""
OpenAI Provider stub.

Placeholder for OpenAI implementation (for v0.3.0+).
"""

from typing import Dict
from .base import LLMProvider, ReviewResult, ProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI API implementation (stub for v0.3.0+)"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo", **kwargs):
        """
        Initialize OpenAI provider.

        Note: This is a stub. Full implementation coming in v0.3.0.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4-turbo)
        """
        raise ProviderError(
            "OpenAI provider not yet implemented. "
            "Coming in v0.3.0. Use 'claude' provider for now."
        )

    def review_code(self, code_snippet: str, context: Dict, metrics: Dict) -> ReviewResult:
        """Not implemented in stub"""
        raise ProviderError("OpenAI provider not yet implemented")

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "openai"

    def get_model_name(self) -> str:
        """Return model name"""
        return "gpt-4-turbo"

    def validate_config(self) -> bool:
        """Not implemented in stub"""
        return False

    def health_check(self) -> bool:
        """Not implemented in stub"""
        return False
