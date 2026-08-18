import pytest
from src.graph_store import TemporalGraphStore

def test_temporal_graph_creation():
    store = TemporalGraphStore()
    
    # Add Supplier A
    store.add_entity("Supplier A", "Supplier", {"location": "Noida"})
    store.add_entity_status_change("Supplier A", "2025-01-01", "Active", "Signed")
    store.add_entity_status_change("Supplier A", "2026-08-10", "Suspended", "Disruption")

    # Add Component X
    store.add_entity("Component X", "Component")

    # Add Relationship
    store.add_relationship("Supplier A", "Component X", "SUPPLIES")
    store.add_relationship_status_change("Supplier A", "Component X", "SUPPLIES", "2025-01-01", "Active")
    store.add_relationship_status_change("Supplier A", "Component X", "SUPPLIES", "2026-08-10", "Suspended")

    # 1. Test state in 2025
    g_2025 = store.get_active_subgraph("2025-06-01")
    assert "Supplier A" in g_2025
    assert "Component X" in g_2025
    assert g_2025.nodes["Supplier A"]["status"] == "Active"
    
    # Assert active relationship
    edge_key = "Supplier A-SUPPLIES-Component X"
    assert g_2025.has_edge("Supplier A", "Component X", key=edge_key)
    assert g_2025.edges["Supplier A", "Component X", edge_key]["status"] == "Active"

    # 2. Test state after suspension in late 2026
    g_2026 = store.get_active_subgraph("2026-09-01")
    # Supplier A node is suspended, so it shouldn't be in the active subgraph
    assert "Supplier A" not in g_2026
    assert "Component X" in g_2026 # Component X is still active
    assert not g_2026.has_edge("Supplier A", "Component X")
