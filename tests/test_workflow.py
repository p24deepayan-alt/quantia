import pytest
import os
import uuid
import sys
from PySide6.QtWidgets import QApplication

from quantia.ui.central.workflow.scene import WorkflowScene
from quantia.ui.central.workflow.nodes_logic import LoadCSVNode, CleanDataNode, ExportCSVNode
from quantia.ui.central.workflow.items import EdgeItem

# Ensure QApplication exists for PySide6 elements
app = QApplication.instance() or QApplication(sys.argv)

def test_workflow_serialization():
    scene = WorkflowScene()
    
    # 1. Create nodes
    load_node = LoadCSVNode(10, 10)
    load_node.file_path = "test.csv"
    load_node._code = "df = pd.read_csv('test.csv')"
    
    clean_node = CleanDataNode(200, 10)
    clean_node._configured_code = "df = df.dropna()"
    clean_node._code = "df = df.dropna()"
    
    export_node = ExportCSVNode(400, 10)
    export_node.file_path = "out.csv"
    export_node._code = "df.to_csv('out.csv')"
    
    scene.addItem(load_node)
    scene.addItem(clean_node)
    scene.addItem(export_node)
    
    # 2. Connect nodes (Load -> Clean -> Export)
    edge1 = EdgeItem(load_node.out_port, clean_node.in_port)
    scene.addItem(edge1)
    load_node.out_port.add_edge(edge1)
    clean_node.in_port.add_edge(edge1)
    edge1.update_positions()
    
    edge2 = EdgeItem(clean_node.out_port, export_node.in_port)
    scene.addItem(edge2)
    clean_node.out_port.add_edge(edge2)
    export_node.in_port.add_edge(edge2)
    edge2.update_positions()
    
    # 3. Serialize
    data = scene.serialize()
    
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2
    
    # 4. Deserialize into new scene
    new_scene = WorkflowScene()
    new_scene.deserialize(data)
    
    # 5. Verify new scene
    nodes = [item for item in new_scene.items() if hasattr(item, "to_dict")]
    edges = [item for item in new_scene.items() if isinstance(item, EdgeItem)]
    
    assert len(nodes) == 3
    assert len(edges) == 2
    
    # Check specific properties
    load_nodes_des = [n for n in nodes if isinstance(n, LoadCSVNode)]
    assert len(load_nodes_des) == 1
    assert load_nodes_des[0].file_path == "test.csv"
    
    clean_nodes_des = [n for n in nodes if isinstance(n, CleanDataNode)]
    assert len(clean_nodes_des) == 1
    assert clean_nodes_des[0]._configured_code == "df = df.dropna()"
    
    export_nodes_des = [n for n in nodes if isinstance(n, ExportCSVNode)]
    assert len(export_nodes_des) == 1
    assert export_nodes_des[0].file_path == "out.csv"

if __name__ == "__main__":
    test_workflow_serialization()
