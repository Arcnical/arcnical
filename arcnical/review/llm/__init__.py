"""
LLM Provider package.

Provides multi-provider LLM abstraction layer.
"""

from .base import (
    LLMProvider,
    ReviewResult,
    ProviderError,
    ProviderUnavailableError,
    ProviderConfigError,
    ProviderTimeoutError,
)
from .claude_provider import ClaudeProvider

try:
    from .openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None  # type: ignore[assignment,misc]

try:
    from .gemini_provider import GeminiProvider
except ImportError:
    GeminiProvider = None  # type: ignore[assignment,misc]

from .mock_provider import MockLLMProvider
from .provider_factory import LLMProviderFactory

__all__ = [
    "LLMProvider",
    "ReviewResult",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderConfigError",
    "ProviderTimeoutError",
    "ClaudeProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "MockLLMProvider",
    "LLMProviderFactory",
]
