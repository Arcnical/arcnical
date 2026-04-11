"""
Updated analyze command with LLM provider support.

This is the UPDATED analyze command that adds:
- --llm-provider flag
- --llm-model flag
- --llm-api-key flag
- Provider configuration loading
- Health check integration

MERGE THIS with your existing arcnical/cli/commands.py analyze command.
Keep all existing functionality, just add the new provider-related code sections.
"""

import click
import logging
from typing import Optional

from arcnical.review.llm.provider_factory import LLMProviderFactory
from arcnical.review.llm.base import ProviderError, ProviderConfigError
from arcnical.cli.config import ProviderConfigLoader
from arcnical.orchestrator.l4_integration import L4Integration

logger = logging.getLogger(__name__)


# SECTION 1: Update the @click.command decorator with new options
# Add these options to your existing analyze command:

NEW_OPTIONS = """
@click.option(
    '--llm-provider',
    type=click.Choice(['claude', 'openai', 'gemini'], case_sensitive=False),
    default='claude',
    envvar='ARCNICAL_LLM_PROVIDER',
    help='LLM provider for L4 analysis (default: claude) [env: ARCNICAL_LLM_PROVIDER]'
)
@click.option(
    '--llm-model',
    type=str,
    default=None,
    envvar='ARCNICAL_LLM_MODEL',
    help='Override default model for provider (e.g., gpt-4-turbo) [env: ARCNICAL_LLM_MODEL]'
)
@click.option(
    '--llm-api-key',
    type=str,
    default=None,
    envvar='ARCNICAL_LLM_API_KEY',
    help='API key for LLM provider [env: ARCNICAL_LLM_API_KEY]'
)
"""

# SECTION 2: Update the analyze function signature
# Add these parameters:

FUNCTION_PARAMS = """
    llm_provider: str,
    llm_model: Optional[str],
    llm_api_key: Optional[str],
"""

# SECTION 3: Add this code INSIDE your analyze function
# (after argument validation, before running analysis)

PROVIDER_SETUP_CODE = """
    # ============================================================
    # SESSION #7: LLM PROVIDER SETUP
    # ============================================================
    
    try:
        # Validate provider is available
        if not LLMProviderFactory.is_available(llm_provider):
            available_providers = ', '.join(LLMProviderFactory.list_providers())
            raise click.BadParameter(
                f"Provider '{llm_provider}' not available. "
                f"Available providers: {available_providers}"
            )
        
        click.echo(f"📊 LLM Provider: {llm_provider}", err=False)
        
        # Load provider configuration
        config_loader = ProviderConfigLoader()
        provider_config = config_loader.get_provider_config(
            provider=llm_provider,
            api_key=llm_api_key,
            model=llm_model
        )
        
        # Validate provider configuration
        if not config_loader.validate_config(llm_provider, provider_config):
            env_key = _get_env_key_for_provider(llm_provider)
            raise click.ClickException(
                f"Invalid configuration for {llm_provider} provider.\\n"
                f"Please provide API key via:\\n"
                f"  1. --llm-api-key flag\\n"
                f"  2. {env_key} environment variable\\n"
                f"  3. {llm_provider} section in l4.yaml config file"
            )
        
        # Create provider instance
        try:
            click.echo(f"🔧 Creating {llm_provider} provider...", err=False)
            llm_provider_instance = LLMProviderFactory.create(
                llm_provider,
                provider_config
            )
        except ProviderConfigError as e:
            raise click.ClickException(
                f"Provider configuration error: {e}"
            )
        except ProviderError as e:
            raise click.ClickException(
                f"Provider error: {e}"
            )
        except Exception as e:
            raise click.ClickException(
                f"Failed to create {llm_provider} provider: {e}"
            )
        
        # Health check provider
        click.echo(f"🏥 Checking provider health...", err=False)
        is_healthy = L4Integration.verify_provider_health(llm_provider_instance)
        
        if not is_healthy:
            if llm_provider == 'claude' and not llm_api_key:
                raise click.ClickException(
                    "Claude provider unavailable. Please check your API key:\\n"
                    "  export ANTHROPIC_API_KEY=sk-...\\n"
                    "  or use: arcnical analyze ./repo --llm-api-key sk-..."
                )
            else:
                click.echo(
                    f"⚠️  Warning: {llm_provider} provider may be unavailable",
                    err=True
                )
        else:
            click.echo(f"✅ {llm_provider} provider healthy", err=False)
    
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Provider setup failed: {e}")
"""

# SECTION 4: Update the L4 review section
# Replace or update your existing L4 review code with this:

L4_REVIEW_CODE = """
    # ============================================================
    # SESSION #7: L4 REVIEW WITH SELECTED PROVIDER
    # ============================================================
    
    try:
        # Create L4 agent with selected provider
        l4_agent = L4Integration.create_l4_agent(llm_provider_instance)
        
        # Run L4 review
        click.echo(f"🔍 Running L4 semantic review with {llm_provider}...", err=False)
        report = L4Integration.run_l4_review(l4_agent, report)
        
        click.echo(f"✅ L4 review complete", err=False)
        
    except Exception as e:
        logger.error(f"L4 review failed: {e}", exc_info=True)
        if force:
            click.echo(f"⚠️  L4 review failed but --force specified, continuing", err=True)
        else:
            raise click.ClickException(f"L4 review failed: {e}")
"""

# SECTION 5: Add this helper function at module level

HELPER_FUNCTION = """
def _get_env_key_for_provider(provider: str) -> str:
    '''Get environment variable name for provider API key.'''
    env_map = {
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GOOGLE_API_KEY',
    }
    return env_map.get(provider.lower(), 'API_KEY')
"""

# ============================================================
# COMPLETE EXAMPLE OF UPDATED FUNCTION
# ============================================================

COMPLETE_EXAMPLE = """
@click.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--depth', type=click.Choice(['quick', 'standard']), default='standard')
@click.option('--force', is_flag=True, help='Force analysis even if qualification fails')
@click.option(
    '--llm-provider',
    type=click.Choice(['claude', 'openai', 'gemini'], case_sensitive=False),
    default='claude',
    envvar='ARCNICAL_LLM_PROVIDER',
    help='LLM provider for L4 analysis'
)
@click.option(
    '--llm-model',
    type=str,
    default=None,
    envvar='ARCNICAL_LLM_MODEL',
    help='Override default model for provider'
)
@click.option(
    '--llm-api-key',
    type=str,
    default=None,
    envvar='ARCNICAL_LLM_API_KEY',
    help='API key for LLM provider'
)
def analyze(
    repo_path: str,
    output_json: bool,
    depth: str,
    force: bool,
    llm_provider: str,
    llm_model: Optional[str],
    llm_api_key: Optional[str]
):
    '''Analyze a repository for architecture quality.
    
    Examples:
        arcnical analyze ./myrepo
        arcnical analyze ./myrepo --llm-provider claude
        arcnical analyze ./myrepo --llm-provider openai --llm-api-key sk-...
        arcnical analyze ./myrepo --depth quick  # Skip L4 (no LLM)
        arcnical analyze ./myrepo --json         # Output as JSON only
    '''
    try:
        # Existing L1-L3 analysis code...
        
        # ============================================================
        # PROVIDER SETUP (add this section)
        # ============================================================
        
        # [INSERT PROVIDER_SETUP_CODE here]
        
        # ============================================================
        # L4 REVIEW (replace existing L4 code with this)
        # ============================================================
        
        # [INSERT L4_REVIEW_CODE here]
        
        # Output results
        if output_json:
            click.echo(report.model_dump_json(indent=2))
        else:
            click.echo("✅ Analysis complete")
            
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Analysis failed: {e}")
"""

print(__doc__)
