"""
PyVis Graph Components for Streamlit Dashboard

Integrates interactive dependency graphs into Streamlit tabs.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, Any, Optional
import networkx as nx
from pyvis.network import Network
import tempfile


class StreamlitGraphComponent:
    """Streamlit components for graph visualization."""

    @staticmethod
    def load_analysis_data() -> Optional[Dict[str, Any]]:
        """Load latest analysis JSON."""
        json_path = Path(".arcnical/results/latest_analysis.json")
        
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def build_dependency_graph(analysis_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Build NetworkX graph from analysis data.
        
        Args:
            analysis_data: Analysis JSON data
            
        Returns:
            NetworkX DiGraph
        """
        graph = nx.DiGraph()
        
        # Extract findings to build dependency relationships
        findings = analysis_data.get("findings", [])
        file_structure = analysis_data.get("file_structure", {})
        
        # Create nodes from file structure
        files = file_structure.get("files", {})
        
        for filename, loc in files.items():
            if isinstance(loc, (int, float)):
                color = StreamlitGraphComponent._get_node_color(loc)
                size = StreamlitGraphComponent._get_node_size(loc)
                
                graph.add_node(
                    filename,
                    title=filename,
                    label=filename,
                    size=size,
                    color=color,
                    loc=loc,
                )
        
        # Create edges from findings
        for finding in findings:
            evidence = finding.get("evidence", {})
            references = evidence.get("references", [])
            
            if len(references) >= 2:
                for i in range(len(references) - 1):
                    source = references[i].get("file", "")
                    target = references[i + 1].get("file", "")
                    
                    if source and target and source != target:
                        edge_color = StreamlitGraphComponent._get_edge_color(
                            finding.get("severity", "Low")
                        )
                        
                        graph.add_edge(
                            source,
                            target,
                            color=edge_color,
                            weight=1,
                            title=finding.get("title", "Dependency"),
                            severity=finding.get("severity", "Low"),
                        )
        
        return graph

    @staticmethod
    def _get_node_color(loc: float) -> str:
        """Get node color based on LOC."""
        if loc <= 100:
            return "#388e3c"  # Green
        elif loc <= 300:
            return "#fbc02d"  # Yellow
        elif loc <= 600:
            return "#ff9800"  # Orange
        else:
            return "#d32f2f"  # Red

    @staticmethod
    def _get_node_size(loc: float) -> int:
        """Get node size based on LOC."""
        if loc <= 0:
            return 10
        if loc <= 100:
            return 15
        if loc <= 300:
            return 25
        if loc <= 600:
            return 35
        return 50

    @staticmethod
    def _get_edge_color(severity: str) -> str:
        """Get edge color based on severity."""
        severity_lower = severity.lower()
        
        if severity_lower == "critical":
            return "#d32f2f"  # Red
        elif severity_lower == "high":
            return "#ff9800"  # Orange
        elif severity_lower == "medium":
            return "#fbc02d"  # Yellow
        else:
            return "#1976d2"  # Blue

    @staticmethod
    def render_pyvis_graph(graph: nx.DiGraph) -> str:
        """
        Render PyVis graph and return HTML path.
        
        Args:
            graph: NetworkX DiGraph
            
        Returns:
            Path to HTML file
        """
        # Create PyVis network
        net = Network(
            height="750px",
            width="100%",
            directed=True,
            physics=True,
            notebook=False,
        )
        
        # Configure physics engine
        net.physics.enabled = True
        net.physics.dynamic_friction = 0.5
        net.physics.stabilization.iterations = 200
        
        # Add nodes
        for node in graph.nodes(data=True):
            node_id = node[0]
            node_attr = node[1]
            
            net.add_node(
                node_id,
                label=node_attr.get("label", node_id),
                title=f"{node_attr.get('label', node_id)} ({int(node_attr.get('loc', 0))} LOC)",
                size=node_attr.get("size", 20),
                color=node_attr.get("color", "#1976d2"),
            )
        
        # Add edges
        for edge in graph.edges(data=True):
            source, target, attr = edge
            net.add_edge(
                source,
                target,
                color=attr.get("color", "#1976d2"),
                title=attr.get("title", "Dependency"),
                weight=attr.get("weight", 1),
            )
        
        # Configure buttons and physics
        net.show_buttons(filter_=["physics"])
        net.toggle_physics(True)
        
        # Save to temporary file
        temp_file = Path(tempfile.gettempdir()) / "arcnical_graph.html"
        net.show(str(temp_file))
        
        return str(temp_file)

    @staticmethod
    def display_graph_in_streamlit(graph: nx.DiGraph) -> None:
        """
        Display graph in Streamlit.
        
        Args:
            graph: NetworkX DiGraph
        """
        if not graph.nodes():
            st.info("No graph data available. Run analysis first.")
            return
        
        # Render PyVis graph
        html_file = StreamlitGraphComponent.render_pyvis_graph(graph)
        
        # Display in Streamlit
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.components.v1.html(html_content, height=800)
        except Exception as e:
            st.error(f"Failed to render graph: {e}")

    @staticmethod
    def display_graph_statistics(graph: nx.DiGraph) -> None:
        """
        Display graph statistics.
        
        Args:
            graph: NetworkX DiGraph
        """
        if not graph.nodes():
            st.info("No graph data available.")
            return
        
        # Calculate statistics
        num_nodes = len(graph.nodes())
        num_edges = len(graph.edges())
        density = nx.density(graph) if num_nodes > 0 else 0
        
        # Calculate average degree
        degrees = dict(graph.degree())
        avg_degree = sum(degrees.values()) / max(num_nodes, 1) if num_nodes > 0 else 0
        
        # Detect circular dependencies
        circular_deps = []
        try:
            circular_deps = list(nx.simple_cycles(graph))
        except:
            pass
        
        # Get hub modules
        hub_modules = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Display in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Files/Modules", num_nodes)
        
        with col2:
            st.metric("Dependencies", num_edges)
        
        with col3:
            st.metric("Graph Density", f"{density:.2f}")
        
        with col4:
            st.metric("Avg Connections", f"{avg_degree:.1f}")
        
        # Hub modules
        st.subheader("🔌 Hub Modules (Most Connected)")
        if hub_modules:
            hub_data = [{"Module": name, "Connections": count} for name, count in hub_modules]
            st.dataframe(hub_data, use_container_width=True)
        else:
            st.info("No hub modules detected.")
        
        # Circular dependencies
        st.subheader("⚠️ Circular Dependencies")
        if circular_deps:
            st.warning(f"Found {len(circular_deps)} circular dependency chains")
            for cycle in circular_deps[:5]:  # Show first 5
                st.code(" → ".join(cycle[:3]) + " → ...", language="text")
        else:
            st.success("✅ No circular dependencies detected!")

    @staticmethod
    def display_legend() -> None:
        """Display graph legend."""
        st.subheader("📊 Graph Legend")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Node Colors (by file complexity):**")
            st.markdown("🟢 Green: < 100 LOC (Simple)")
            st.markdown("🟡 Yellow: 100-300 LOC (Medium)")
            st.markdown("🟠 Orange: 300-600 LOC (Complex)")
            st.markdown("🔴 Red: > 600 LOC (Very Complex)")
        
        with col2:
            st.markdown("**Node Size (by lines of code):**")
            st.markdown("Small: Few lines of code")
            st.markdown("Large: Many lines of code")
        
        st.markdown("**Edge Colors (by issue severity):**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("🔴 Red: Critical")
        with col2:
            st.markdown("🟠 Orange: High")
        with col3:
            st.markdown("🟡 Yellow: Medium")
        with col4:
            st.markdown("🔵 Blue: Normal dependency")
