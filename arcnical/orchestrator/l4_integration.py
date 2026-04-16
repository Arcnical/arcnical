"""
L4 agent integration with provider.

Integrates L4 review agent with selected LLM provider.
"""

import logging
from typing import Optional

from arcnical.review.llm.base import LLMProvider
from arcnical.review.l4_refactored import L4ReviewAgent
from arcnical.schema import Report

logger = logging.getLogger(__name__)


class L4Integration:
    """Integrate L4 agent with selected provider"""

    @staticmethod
    def create_l4_agent(provider: LLMProvider) -> L4ReviewAgent:
        """
        Create L4 agent with provider.

        Args:
            provider: LLMProvider instance (Claude, OpenAI, Gemini, etc.)

        Returns:
            L4ReviewAgent instance

        Raises:
            ValueError: If provider is None
        """
        if provider is None:
            raise ValueError("LLMProvider is required")

        logger.info(
            f"Creating L4 agent with {provider.get_provider_name()} "
            f"({provider.get_model_name()})"
        )

        return L4ReviewAgent(provider)

    @staticmethod
    def run_l4_review(l4_agent: L4ReviewAgent, report: Report) -> Report:
        """
        Run L4 review with agent.

        Args:
            l4_agent: L4ReviewAgent instance
            report: Report from L1-L3 analysis

        Returns:
            Updated report with L4 findings

        Raises:
            Exception: If L4 review fails
        """
        try:
            logger.info(
                f"Running L4 review with {l4_agent.get_provider_name()} "
                f"({l4_agent.get_model_name()})"
            )

            updated_report = l4_agent.review(report)

            # Update model name in metadata if available
            if (
                hasattr(updated_report, "metadata")
                and updated_report.metadata is not None
            ):
                updated_report.metadata.model = l4_agent.get_model_name()

            logger.info(
                f"L4 review complete. "
                f"Added {len(updated_report.recommendations)} recommendations. "
                f"Total: {len(updated_report.recommendations)}"
            )

            return updated_report

        except Exception as e:
            logger.error(f"L4 review failed: {e}", exc_info=True)
            raise

    @staticmethod
    def verify_provider_health(provider: LLMProvider) -> bool:
        """
        Verify provider is healthy and accessible.

        Args:
            provider: LLMProvider instance

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            logger.info(f"Checking {provider.get_provider_name()} provider health...")
            is_healthy = provider.health_check()

            if is_healthy:
                logger.info(
                    f"{provider.get_provider_name()} provider is healthy"
                )
            else:
                logger.warning(
                    f"{provider.get_provider_name()} provider may be unavailable"
                )

            return is_healthy

        except Exception as e:
            logger.error(
                f"Health check failed for {provider.get_provider_name()}: {e}"
            )
            return False
