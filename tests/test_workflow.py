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

def test_extended_workflow_serialization():
    from quantia.ui.central.workflow.nodes_logic import PCANode, LinearRegressionNode, SaveReportNode
    scene = WorkflowScene()
    
    pca = PCANode(10, 10)
    pca._configured_code = "# pca code"
    
    reg = LinearRegressionNode(200, 10)
    reg._configured_code = "# regression code"
    
    rep = SaveReportNode(400, 10)
    rep.file_path = "report.html"
    
    scene.addItem(pca)
    scene.addItem(reg)
    scene.addItem(rep)
    
    # PCA -> Reg -> Rep
    e1 = EdgeItem(pca.out_port, reg.in_port)
    scene.addItem(e1)
    pca.out_port.add_edge(e1)
    reg.in_port.add_edge(e1)
    
    e2 = EdgeItem(reg.out_port, rep.in_port)
    scene.addItem(e2)
    reg.out_port.add_edge(e2)
    rep.in_port.add_edge(e2)
    
    data = scene.serialize()
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2
    
    new_scene = WorkflowScene()
    new_scene.deserialize(data)
    
    nodes = [item for item in new_scene.items() if hasattr(item, "to_dict")]
    edges = [item for item in new_scene.items() if isinstance(item, EdgeItem)]
    
    assert len(nodes) == 3
    assert len(edges) == 2
    
    pca_nodes = [n for n in nodes if isinstance(n, PCANode)]
    assert len(pca_nodes) == 1
    assert pca_nodes[0]._configured_code == "# pca code"
    
    reg_nodes = [n for n in nodes if isinstance(n, LinearRegressionNode)]
    assert len(reg_nodes) == 1
    assert reg_nodes[0]._configured_code == "# regression code"
    
    rep_nodes = [n for n in nodes if isinstance(n, SaveReportNode)]
    assert len(rep_nodes) == 1
    assert rep_nodes[0].file_path == "report.html"

if __name__ == "__main__":
    test_workflow_serialization()
    test_extended_workflow_serialization()
