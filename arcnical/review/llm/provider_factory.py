"""
LLM Provider factory.

Factory pattern for creating LLM provider instances.
"""

from typing import Dict, Type, List
import importlib

from .base import LLMProvider, ProviderError


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""

    _providers: Dict[str, str] = {
        "claude": "arcnical.review.llm.claude_provider.ClaudeProvider",
        "openai": "arcnical.review.llm.openai_provider.OpenAIProvider",
        "gemini": "arcnical.review.llm.gemini_provider.GeminiProvider",
    }

    _loaded_providers: Dict[str, Type[LLMProvider]] = {}

    @staticmethod
    def create(provider_name: str, config: Dict) -> LLMProvider:
        """
        Create a provider instance.

        Args:
            provider_name: Name of provider (claude, openai, gemini)
            config: Configuration dict for the provider

        Returns:
            LLMProvider instance

        Raises:
            ProviderError: If provider is unknown or creation fails
        """
        provider_name = provider_name.lower().strip()

        if provider_name not in LLMProviderFactory._providers:
            available = ", ".join(LLMProviderFactory.list_providers())
            raise ProviderError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {available}"
            )

        try:
            # Load provider class if not already loaded
            if provider_name not in LLMProviderFactory._loaded_providers:
                provider_path = LLMProviderFactory._providers[provider_name]
                module_path, class_name = provider_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                provider_class = getattr(module, class_name)
                LLMProviderFactory._loaded_providers[provider_name] = provider_class
            else:
                provider_class = LLMProviderFactory._loaded_providers[provider_name]

            # Create instance
            return provider_class(**config)

        except ProviderError:
            raise
        except ImportError as e:
            raise ProviderError(
                f"Cannot import {provider_name} provider (not yet implemented): {e}"
            )
        except Exception as e:
            raise ProviderError(f"Failed to create {provider_name} provider: {e}")

    @staticmethod
    def list_providers() -> List[str]:
        """
        List available providers.

        Returns:
            List of provider names
        """
        return list({
            **LLMProviderFactory._providers,
            **LLMProviderFactory._loaded_providers
        }.keys())

    @staticmethod
    def register_provider(
        name: str, provider_class: Type[LLMProvider], module_path: str = None
    ):
        """
        Register a new provider.

        Args:
            name: Provider name
            provider_class: Provider class (implements LLMProvider)
            module_path: Full module path (optional, for lazy loading)
        """
        name = name.lower().strip()

        if module_path:
            LLMProviderFactory._providers[name] = module_path
        else:
            LLMProviderFactory._loaded_providers[name] = provider_class

    @staticmethod
    def is_available(provider_name: str) -> bool:
        """
        Check if provider is available.

        Args:
            provider_name: Name of provider

        Returns:
            True if provider is available, False otherwise
        """
        provider_name = provider_name.lower().strip()
        return (
            provider_name in LLMProviderFactory._providers
            or provider_name in LLMProviderFactory._loaded_providers
        )
