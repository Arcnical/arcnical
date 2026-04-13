"""
Enhanced Sidebar Components for Arcnical Dashboard - Phase 4

Provides:
- Provider selector (Claude/OpenAI/Gemini)
- Depth selector (Quick/Standard)
- Re-run analysis button
- Status display with live updates
- Execution metrics
"""

import streamlit as st
from typing import Tuple
from datetime import datetime


class SidebarController:
    """Controls sidebar state and interactions."""

    @staticmethod
    def initialize_session_state() -> None:
        """Initialize session state variables."""
        if "provider" not in st.session_state:
            st.session_state.provider = "claude"
        
        if "depth" not in st.session_state:
            st.session_state.depth = "standard"
        
        if "status" not in st.session_state:
            st.session_state.status = "Ready"
        
        if "last_run_time" not in st.session_state:
            st.session_state.last_run_time = None
        
        if "execution_time" not in st.session_state:
            st.session_state.execution_time = None
        
        if "findings_count" not in st.session_state:
            st.session_state.findings_count = 0
        
        if "re_run_clicked" not in st.session_state:
            st.session_state.re_run_clicked = False

    @staticmethod
    def render_sidebar() -> Tuple[str, str, bool]:
        """
        Render sidebar with all controls.
        
        Returns:
            Tuple of (provider, depth, re_run_clicked)
        """
        SidebarController.initialize_session_state()
        
        with st.sidebar:
            st.markdown("## ⚙️ Analysis Controls")
            st.divider()
            
            # Provider Selector
            st.markdown("### 🤖 LLM Provider")
            provider_options = {
                "Claude": "claude",
                "OpenAI": "openai",
                "Gemini": "gemini"
            }
            
            provider_display = st.radio(
                "Select LLM Provider",
                options=list(provider_options.keys()),
                index=0 if st.session_state.provider == "claude" else 1,
                label_visibility="collapsed",
                key="provider_radio",
                horizontal=False,
            )
            
            st.session_state.provider = provider_options[provider_display]
            
            # Provider info
            provider_info = {
                "Claude": "🔵 Anthropic Claude - Recommended",
                "OpenAI": "🟢 OpenAI GPT - Coming soon",
                "Gemini": "🟡 Google Gemini - Coming soon"
            }
            st.caption(provider_info.get(provider_display, ""))
            
            st.divider()
            
            # Depth Selector
            st.markdown("### 📊 Analysis Depth")
            depth_options = {
                "Quick": "quick",
                "Standard": "standard"
            }
            
            depth_display = st.radio(
                "Select Analysis Depth",
                options=list(depth_options.keys()),
                index=1 if st.session_state.depth == "standard" else 0,
                label_visibility="collapsed",
                key="depth_radio",
                horizontal=False,
            )
            
            st.session_state.depth = depth_options[depth_display]
            
            # Depth info
            depth_info = {
                "Quick": "⚡ L1-L3 only (no LLM)",
                "Standard": "🔬 Full L1-L4 (with LLM)"
            }
            st.caption(depth_info.get(depth_display, ""))
            
            st.divider()
            
            # Re-run Button
            st.markdown("### 🔄 Execute Analysis")
            
            re_run_clicked = st.button(
                "🔄 Re-run Analysis",
                use_container_width=True,
                type="primary",
                key="re_run_button",
                help="Re-analyze repository with current settings"
            )
            
            if re_run_clicked:
                st.session_state.re_run_clicked = True
            
            st.divider()
            
            # Status Display
            st.markdown("### 📡 Status")
            
            # Status indicator
            status_colors = {
                "Ready": "🟢",
                "Running": "🟡",
                "Complete": "🟢",
                "Error": "🔴"
            }
            
            status_emoji = status_colors.get(st.session_state.status, "⚪")
            st.markdown(f"**{status_emoji} {st.session_state.status}**")
            
            # Status details
            st.markdown("---")
            
            # Last run time
            if st.session_state.last_run_time:
                last_run = st.session_state.last_run_time
                st.markdown(f"**Last Run:** {last_run}")
            else:
                st.markdown("**Last Run:** Never")
            
            # Execution time
            if st.session_state.execution_time:
                st.markdown(f"**Time:** {st.session_state.execution_time:.2f}s")
            else:
                st.markdown("**Time:** —")
            
            # Findings count
            st.markdown(f"**Findings:** {st.session_state.findings_count}")
            
            st.divider()
            
            # Settings Summary
            st.markdown("### ⚙️ Current Settings")
            settings_text = f"""
- **Provider:** {st.session_state.provider.capitalize()}
- **Depth:** {st.session_state.depth.capitalize()}
- **Status:** {st.session_state.status}
            """
            st.markdown(settings_text)
            
            return st.session_state.provider, st.session_state.depth, re_run_clicked

    @staticmethod
    def update_status(status: str, execution_time: float = None, findings_count: int = None) -> None:
        """
        Update sidebar status display.
        
        Args:
            status: Status string (Ready, Running, Complete, Error)
            execution_time: Execution time in seconds
            findings_count: Number of findings
        """
        st.session_state.status = status
        
        if execution_time is not None:
            st.session_state.execution_time = execution_time
        
        if findings_count is not None:
            st.session_state.findings_count = findings_count
        
        if status in ["Complete", "Error"]:
            st.session_state.last_run_time = datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def get_cli_command(repo_path: str = "./test_repo") -> str:
        """
        Generate CLI command based on current settings.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            CLI command string
        """
        provider = st.session_state.provider
        depth = st.session_state.depth
        
        cmd = f"python -m arcnical analyze {repo_path}"
        cmd += f" --depth {depth}"
        cmd += f" --llm-provider {provider}"
        
        if depth == "standard":
            cmd += " --llm-api-key sk-ant-..."
        
        return cmd
