"""
Sidebar components for Arcnical dashboard.

Provides:
- Provider selector (Claude/OpenAI/Gemini)
- Depth selector (Standard/Quick)
- Re-run button
- Status display
"""

import streamlit as st
from typing import Tuple


def render_sidebar() -> Tuple[str, str, bool]:
    """
    Render right sidebar with controls.
    
    Returns:
        Tuple of (provider, depth, re_run_clicked)
    """
    
    # Provider selector
    st.markdown("**Provider**")
    providers = ["Claude", "OpenAI", "Gemini"]
    provider = st.radio(
        "Select LLM Provider",
        providers,
        index=0,
        label_visibility="collapsed",
        horizontal=False,
    )
    
    st.divider()
    
    # Depth selector
    st.markdown("**Depth**")
    depths = ["Standard", "Quick"]
    depth = st.radio(
        "Select Analysis Depth",
        depths,
        index=0,
        label_visibility="collapsed",
        horizontal=False,
    )
    
    st.divider()
    
    # Re-run button
    re_run_clicked = st.button(
        "🔄 Re-run Analysis",
        use_container_width=True,
        type="primary",
        key="re_run_button",
    )
    
    st.divider()
    
    # Status display
    st.markdown("**Status**")
    
    # Status indicator
    status_color = "🟢" if st.session_state.get("status") == "Ready" else "🟡"
    st.markdown(f"{status_color} **{st.session_state.get('status', 'Ready')}**")
    
    # Status details
    st.markdown("""
    <div style="font-size: 12px; color: #666;">
    Last run: 2 min ago<br>
    Provider: Claude<br>
    Model: sonnet-4-6<br>
    Time: 2.34s
    </div>
    """, unsafe_allow_html=True)
    
    return provider, depth, re_run_clicked


def render_header_with_counts(critical: int, high: int, medium: int, low: int, health_score: int) -> None:
    """
    Render header with finding counts and health circle.
    
    Args:
        critical: Count of critical findings
        high: Count of high findings
        medium: Count of medium findings
        low: Count of low findings
        health_score: Health score (0-100)
    """
    
    col1, col2 = st.columns([0.85, 0.15])
    
    with col1:
        # Severity counts
        st.markdown(f"""
        <div style="display: flex; gap: 16px; align-items: center; padding: 16px; background: #f5f5f5; border-radius: 8px;">
            <span style="color: #d32f2f; font-weight: 600; font-size: 13px;">🔴 {critical} CRITICAL</span>
            <span style="color: #ff9800; font-weight: 600; font-size: 13px;">🟠 {high} HIGH</span>
            <span style="color: #fbc02d; font-weight: 600; font-size: 13px;">🟡 {medium} MEDIUM</span>
            <span style="color: #388e3c; font-weight: 600; font-size: 13px;">🟢 {low} LOW</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Health circle
        st.markdown(f"""
        <div style="
            width: 80px; 
            height: 80px; 
            border: 4px solid #ff9800; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            margin: 0 auto;
        ">
            <div style="text-align: center;">
                <div style="font-size: 28px; font-weight: 600; color: #ff9800;">{health_score}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
