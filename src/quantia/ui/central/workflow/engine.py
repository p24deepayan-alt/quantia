"""Execution engine for Workflow Builder."""

from __future__ import annotations

import pandas as pd
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from quantia.ui.central.workflow.scene import WorkflowScene
    from quantia.ui.central.workflow.nodes_logic import BaseLogicNode


class WorkflowEngine:
    """Traverses a workflow scene and executes logic nodes."""
    
    def __init__(self, scene: WorkflowScene) -> None:
        self.scene = scene

    def get_nodes(self) -> list[BaseLogicNode]:
        """Extract all BaseLogicNodes from the scene."""
        from quantia.ui.central.workflow.nodes_logic import BaseLogicNode
        nodes = []
        for item in self.scene.items():
            if isinstance(item, BaseLogicNode):
                nodes.append(item)
        return nodes

    def build_dag(self) -> tuple[list[BaseLogicNode], bool]:
        """Perform topological sort on the nodes."""
        nodes = self.get_nodes()
        
        # Build adjacency list: node -> list of nodes it points to
        graph = {node: [] for node in nodes}
        in_degree = {node: 0 for node in nodes}
        
        for node in nodes:
            for edge in node.out_port.edges:
                if edge.dest_port and edge.dest_port.node:
                    dest_node = edge.dest_port.node
                    graph[node].append(dest_node)
                    in_degree[dest_node] += 1
                    
        # Topological Sort (Kahn's Algorithm)
        queue = [n for n in nodes if in_degree[n] == 0]
        sorted_nodes = []
        
        while queue:
            current = queue.pop(0)
            sorted_nodes.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(sorted_nodes) != len(nodes):
            return [], False  # Cycle detected
            
        return sorted_nodes, True

    def run(self) -> str:
        """Execute the DAG and return the full script."""
        sorted_nodes, is_dag = self.build_dag()
        if not is_dag:
            return "# Error: Cycle detected in workflow graph."
            
        full_script = ["# Quantia Workflow Execution", "import pandas as pd", ""]
        
        # Reset states
        for node in sorted_nodes:
            node.output_df = None
            
        for node in sorted_nodes:
            # Gather inputs
            input_dfs = []
            for edge in node.in_port.edges:
                if edge.source_port and hasattr(edge.source_port.node, "output_df"):
                    src_df = edge.source_port.node.output_df
                    if src_df is not None:
                        input_dfs.append(src_df)
                        
            # Run node logic
            try:
                node.run_logic(input_dfs)
                script = node.get_code()
                if script:
                    full_script.append(f"# --- {node.title_text} ---")
                    full_script.append(script)
                    full_script.append("")
            except Exception as e:
                full_script.append(f"# Error executing {node.title_text}: {str(e)}")
                break
                
        return "\n".join(full_script)
