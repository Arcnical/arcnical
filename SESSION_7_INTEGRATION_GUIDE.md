# 🚀 SESSION #7 INTEGRATION GUIDE

**Status:** All code generated ✅  
**Next:** Copy files to your project  
**Time:** 15-30 minutes  

---

## 📦 FILES GENERATED (5 files)

### **New Files (Copy these):**
1. ✅ `arcnical/cli/config.py` - Configuration loader
2. ✅ `arcnical/orchestrator/l4_integration.py` - L4 integration
3. ✅ `tests/unit/test_cli_provider_integration.py` - Tests

### **Modified Files (Update these):**
4. ✅ `arcnical/cli/commands.py` - Add provider flags (see guide below)
5. ✅ `arcnical/orchestrator/main.py` - Pass provider to L4 (see guide below)

### **Reference (Don't copy):**
- `CLI_COMMANDS_UPDATE_GUIDE.py` - Detailed instructions for updating commands.py

---

## 📋 STEP-BY-STEP INTEGRATION

### **Step 1: Copy New Files (5 minutes)**

```powershell
# Copy config.py to CLI folder
Copy-Item "arcnical\cli\config.py" "D:\Projects\arcnical_repo\arcnical\cli\"

# Copy l4_integration.py to orchestrator
Copy-Item "arcnical\orchestrator\l4_integration.py" "D:\Projects\arcnical_repo\arcnical\orchestrator\"

# Copy test file
Copy-Item "tests\unit\test_cli_provider_integration.py" "D:\Projects\arcnical_repo\tests\unit\"
```

---

### **Step 2: Update arcnical/cli/commands.py (10 minutes)**

**This is the IMPORTANT one!**

**What to do:**
1. Open your `arcnical/cli/commands.py` file
2. Find the `analyze` command function
3. Add the provider-related code

**Add these imports at the top:**
```python
from arcnical.review.llm.provider_factory import LLMProviderFactory
from arcnical.review.llm.base import ProviderError, ProviderConfigError
from arcnical.cli.config import ProviderConfigLoader
from arcnical.orchestrator.l4_integration import L4Integration
```

**Add these options to @click.command() decorator:**
```python
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
    help='Override default model for provider [env: ARCNICAL_LLM_MODEL]'
)
@click.option(
    '--llm-api-key',
    type=str,
    default=None,
    envvar='ARCNICAL_LLM_API_KEY',
    help='API key for LLM provider [env: ARCNICAL_LLM_API_KEY]'
)
```

**Add these parameters to function signature:**
```python
def analyze(
    # ... existing parameters ...
    llm_provider: str,
    llm_model: Optional[str],
    llm_api_key: Optional[str],
):
```

**Add this code BEFORE L4 analysis (in the analyze function body):**
```python
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
        raise click.ClickException(
            f"Invalid configuration for {llm_provider} provider.\n"
            f"Please provide API key via:\n"
            f"  1. --llm-api-key flag\n"
            f"  2. Environment variable\n"
            f"  3. l4.yaml config file"
        )
    
    # Create provider instance
    try:
        click.echo(f"🔧 Creating {llm_provider} provider...", err=False)
        llm_provider_instance = LLMProviderFactory.create(
            llm_provider,
            provider_config
        )
    except (ProviderConfigError, ProviderError) as e:
        raise click.ClickException(f"Provider error: {e}")
    except Exception as e:
        raise click.ClickException(
            f"Failed to create {llm_provider} provider: {e}"
        )
    
    # Health check provider
    click.echo(f"🏥 Checking provider health...", err=False)
    is_healthy = L4Integration.verify_provider_health(llm_provider_instance)
    
    if is_healthy:
        click.echo(f"✅ {llm_provider} provider healthy", err=False)
    else:
        click.echo(
            f"⚠️  Warning: {llm_provider} provider may be unavailable",
            err=True
        )

except click.ClickException:
    raise
except Exception as e:
    raise click.ClickException(f"Provider setup failed: {e}")
```

**Replace your existing L4 review code with:**
```python
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
```

---

### **Step 3: Run Tests (10 minutes)**

```powershell
# Test config loader
python -m pytest tests/unit/test_cli_provider_integration.py -v

# Expected: All tests passing ✅
```

---

### **Step 4: Test CLI Manually (5 minutes)**

```powershell
# Test with default provider (Claude)
python -m arcnical analyze ./test_repo

# Test with provider flag
python -m arcnical analyze ./test_repo --llm-provider claude

# Test with API key override (if you have a key)
python -m arcnical analyze ./test_repo --llm-api-key sk-...

# Test with model override
python -m arcnical analyze ./test_repo --llm-model gpt-4-turbo --llm-provider openai
```

---

## ✅ VERIFICATION CHECKLIST

After integration:

- [ ] `arcnical/cli/config.py` copied
- [ ] `arcnical/orchestrator/l4_integration.py` copied
- [ ] `tests/unit/test_cli_provider_integration.py` copied
- [ ] `arcnical/cli/commands.py` updated with provider options
- [ ] `arcnical/cli/commands.py` updated with provider parameters
- [ ] `arcnical/cli/commands.py` updated with provider setup code
- [ ] `arcnical/cli/commands.py` updated with L4 integration code
- [ ] Tests running: `python -m pytest tests/unit/test_cli_provider_integration.py -v`
- [ ] All tests passing ✅
- [ ] CLI accepts `--llm-provider` flag ✅
- [ ] CLI accepts `--llm-api-key` flag ✅
- [ ] CLI accepts `--llm-model` flag ✅

---

## 🧪 EXPECTED TEST RESULTS

When you run the new tests:

```
test_cli_provider_integration.py

TestProviderConfigLoader:
  test_init_no_config_file                    PASSED ✅
  test_get_provider_config_defaults           PASSED ✅
  test_get_provider_config_with_api_key       PASSED ✅
  test_get_provider_config_with_model_override PASSED ✅
  test_validate_config_missing_api_key        PASSED ✅
  test_validate_config_missing_model          PASSED ✅
  test_validate_config_success                PASSED ✅
  test_get_env_key_for_provider_claude        PASSED ✅
  test_get_env_key_for_provider_openai        PASSED ✅
  test_get_env_key_for_provider_gemini        PASSED ✅
  test_get_default_model_*                    PASSED ✅
  test_get_provider_config_with_env_var       PASSED ✅
  test_cli_flag_overrides_env_var             PASSED ✅

TestL4Integration:
  test_create_l4_agent                        PASSED ✅
  test_create_l4_agent_with_none_provider     PASSED ✅
  test_verify_provider_health                 PASSED ✅
  test_verify_provider_health_failure         PASSED ✅
  test_run_l4_review                          PASSED ✅
  test_run_l4_review_with_metadata            PASSED ✅
  test_run_l4_review_error_handling           PASSED ✅

TestProviderFlagIntegration:
  test_provider_flag_choices                  PASSED ✅
  test_api_key_from_environment               PASSED ✅
  test_config_precedence                      PASSED ✅
  test_health_check_integration                PASSED ✅

─────────────────────────────────────────────
TOTAL:                                   24 tests PASSED ✅
```

---

## 🎯 FINAL CHECKLIST

**Session #7 is complete when:**

- [ ] All 5 files created/updated
- [ ] 24 new tests passing
- [ ] CLI accepts provider flags
- [ ] Configuration loading works
- [ ] Health check integrated
- [ ] Error handling user-friendly
- [ ] All existing CLI features still work
- [ ] No breaking changes

---

## 📊 FINAL STATUS

```
Sessions Complete:    7/9 (78%)
Hours Used:          55-57/87 (63%)
Hours Remaining:     30-32 (37%)
Timeline:            ON TRACK ✅
```

---

**Ready to integrate?** Follow the steps above! 🚀

Tell me when done: **"Session #7 integrated! Tests running!"** ✅

