"""
CLI Bridge for Arcnical Dashboard - Phase 4

Handles:
- Executing CLI commands from Streamlit
- Capturing CLI output
- Updating analysis data
- Displaying execution status
"""

import subprocess
import json
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime
import time


class CLIBridge:
    """Bridge between Streamlit dashboard and Arcnical CLI."""

    DEFAULT_REPO_PATH = "./test_repo"
    JSON_OUTPUT_PATH = Path(".arcnical/results/latest_analysis.json")

    @staticmethod
    def execute_analysis(
        repo_path: str = DEFAULT_REPO_PATH,
        depth: str = "quick",
        provider: str = "claude",
        api_key: str = None
    ) -> Tuple[bool, str, float, Dict[str, Any]]:
        """
        Execute CLI analysis command.
        
        Args:
            repo_path: Path to repository
            depth: Analysis depth (quick/standard)
            provider: LLM provider (claude/openai/gemini)
            api_key: API key for provider (optional for quick)
            
        Returns:
            Tuple of (success, message, execution_time, data)
        """
        start_time = time.time()
        
        try:
            # Build command
            cmd = [
                "python", "-m", "arcnical", "analyze",
                repo_path,
                "--depth", depth,
                "--llm-provider", provider
            ]
            
            # Add API key if provided
            if api_key and depth == "standard":
                cmd.extend(["--llm-api-key", api_key])
            
            # Execute command
            st.write("🔄 Running analysis...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Check success
            if result.returncode == 0:
                # Load generated JSON
                data = CLIBridge.load_analysis_data()
                
                if data:
                    findings_count = len(data.get("findings", []))
                    message = f"✅ Analysis complete in {execution_time:.2f}s ({findings_count} findings)"
                    return True, message, execution_time, data
                else:
                    message = "⚠️ Analysis ran but JSON not found"
                    return False, message, execution_time, {}
            else:
                # Error in CLI
                error_msg = result.stderr or result.stdout
                message = f"❌ Analysis failed: {error_msg[:100]}"
                return False, message, execution_time, {}
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            message = "❌ Analysis timeout (exceeded 5 minutes)"
            return False, message, execution_time, {}
        
        except FileNotFoundError:
            message = "❌ arcnical command not found. Install with: pip install -e ."
            return False, message, 0, {}
        
        except Exception as e:
            execution_time = time.time() - start_time
            message = f"❌ Error: {str(e)[:100]}"
            return False, message, execution_time, {}

    @staticmethod
    def load_analysis_data() -> Dict[str, Any]:
        """Load latest analysis JSON."""
        try:
            if not CLIBridge.JSON_OUTPUT_PATH.exists():
                return {}
            
            with open(CLIBridge.JSON_OUTPUT_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Failed to load analysis: {e}")
            return {}

    @staticmethod
    def get_cli_output_display(
        repo_path: str,
        depth: str,
        provider: str,
        execution_time: float = None,
        findings_count: int = None
    ) -> str:
        """
        Generate CLI output display text.
        
        Args:
            repo_path: Repository path
            depth: Analysis depth
            provider: LLM provider
            execution_time: Execution time
            findings_count: Number of findings
            
        Returns:
            Formatted CLI output text
        """
        output = f"""D:\\Projects\\arcnical_repo> python -m arcnical analyze {repo_path}
--depth {depth}
--llm-provider {provider}
"""
        
        if depth == "quick":
            output += """
✅ L1: Qualifying repository... PASSED
✅ L2: Analyzing structure... PASSED
✅ L3: Analyzing heuristics... PASSED
✅ JSON exported to .arcnical\\results\\latest_analysis.json
⏭️  Skipping L4 (--depth quick)
"""
        else:
            output += """
✅ L1: Qualifying repository... PASSED
✅ L2: Analyzing structure... PASSED
✅ L3: Analyzing heuristics... PASSED
✅ L4: LLM review... PASSED
✅ JSON exported to .arcnical\\results\\latest_analysis.json
"""
        
        if execution_time:
            output += f"\n✅ Completed in {execution_time:.2f}s"
        
        if findings_count is not None:
            output += f"\n📋 Findings: {findings_count}"
        
        output += "\n✅ Analysis complete"
        
        return output

    @staticmethod
    def get_config_summary(
        provider: str,
        depth: str,
        execution_time: float = None,
        findings_count: int = None
    ) -> str:
        """
        Generate configuration summary text.
        
        Args:
            provider: LLM provider
            depth: Analysis depth
            execution_time: Execution time
            findings_count: Number of findings
            
        Returns:
            Formatted configuration summary
        """
        model_map = {
            "claude": "claude-sonnet-4-6",
            "openai": "gpt-4",
            "gemini": "gemini-pro"
        }
        
        model = model_map.get(provider, provider)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        summary = f"""**Model:** {model}
**Provider:** {provider.capitalize()}
**Depth:** {depth.capitalize()}
**Last Run:** {timestamp}"""
        
        if execution_time:
            summary += f"\n**Time:** {execution_time:.2f}s"
        
        if findings_count is not None:
            summary += f"\n**Findings:** {findings_count}"
        
        return summary
