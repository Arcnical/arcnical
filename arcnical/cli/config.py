"""
Provider configuration management.

Loads and manages LLM provider configuration from l4.yaml and environment variables.
"""

import os
from typing import Dict, Optional
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class ProviderConfigLoader:
    """Load and manage provider configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to l4.yaml config file (optional)
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        logger.debug(f"Config loaded from: {self.config_path or 'defaults'}")

    def _find_config_file(self) -> Optional[str]:
        """
        Find l4.yaml in default locations.

        Returns:
            Path to config file or None if not found
        """
        candidates = [
            Path(".arcnical/l4.yaml"),
            Path("~/.arcnical/l4.yaml").expanduser(),
            Path("arcnical/layers/l4.yaml"),
            Path(".").resolve() / ".arcnical" / "l4.yaml",
        ]

        for path in candidates:
            if path.exists():
                logger.debug(f"Found config at: {path}")
                return str(path)

        logger.debug("No l4.yaml config file found, using defaults")
        return None

    def _load_config(self) -> Dict:
        """
        Load configuration from file.

        Returns:
            Dict with configuration (empty dict if no file found)
        """
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    logger.info(f"Loaded config from {self.config_path}")
                    return config
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
                return {}

        return {}

    def get_provider_config(
        self,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict:
        """
        Get provider configuration.

        Merges configuration from:
        1. l4.yaml file (provider-specific section)
        2. Environment variables (override file)
        3. Command-line arguments (highest priority)

        Args:
            provider: Provider name (claude, openai, gemini)
            api_key: Optional override for API key
            model: Optional override for model

        Returns:
            Dict with provider configuration
        """
        # Start with provider-specific config from file
        config = self.config.get(provider, {}).copy() if self.config else {}

        # Ensure api_key exists in config
        if "api_key" not in config:
            config["api_key"] = None

        # Get API key from sources (in priority order)
        if api_key:
            # CLI argument wins
            config["api_key"] = api_key
        else:
            # Try environment variable
            env_key = self._get_env_key_for_provider(provider)
            if env_key and os.getenv(env_key):
                config["api_key"] = os.getenv(env_key)

        # Override model if provided
        if model:
            config["model"] = model
        elif "model" not in config:
            # Use default model for provider
            config["model"] = self._get_default_model(provider)

        # Ensure other required fields have defaults
        if "temperature" not in config:
            config["temperature"] = 0
        if "max_tokens" not in config:
            config["max_tokens"] = 4000
        if "timeout" not in config:
            config["timeout"] = 180

        logger.debug(f"Config for {provider}: model={config.get('model')}, has_api_key={bool(config.get('api_key'))}")

        return config

    def validate_config(self, provider: str, config: Dict) -> bool:
        """
        Validate provider configuration.

        Args:
            provider: Provider name
            config: Configuration dict

        Returns:
            True if valid, False otherwise
        """
        # API key is required
        if not config.get("api_key"):
            logger.warning(f"No API key provided for {provider}")
            return False

        # Model is required
        if not config.get("model"):
            logger.warning(f"No model specified for {provider}")
            return False

        logger.debug(f"Config validation passed for {provider}")
        return True

    def _get_env_key_for_provider(self, provider: str) -> Optional[str]:
        """
        Get environment variable name for provider API key.

        Args:
            provider: Provider name (claude, openai, gemini)

        Returns:
            Environment variable name or None
        """
        env_map = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        return env_map.get(provider.lower())

    def _get_default_model(self, provider: str) -> str:
        """
        Get default model for provider.

        Args:
            provider: Provider name

        Returns:
            Default model name
        """
        defaults = {
            "claude": "claude-sonnet-4-6",
            "openai": "gpt-4-turbo",
            "gemini": "gemini-pro",
        }
        return defaults.get(provider.lower(), "unknown")

    def get_all_providers(self) -> list:
        """
        Get list of configured providers.

        Returns:
            List of provider names
        """
        return list(self.config.keys()) if self.config else []

    def get_fallback_provider(self) -> Optional[str]:
        """
        Get fallback provider if primary unavailable.

        Returns:
            Fallback provider name or None
        """
        if self.config and "fallback_provider" in self.config:
            return self.config.get("fallback_provider")
        return None
