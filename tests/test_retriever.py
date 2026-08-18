import pytest
from src.mock_data import get_preconfigured_graph, MOCK_DOCUMENTS
from src.retriever import GraphRetriever, DocumentVectorRetriever, HybridGraphRetriever

def test_entity_identification():
    store = get_preconfigured_graph()
    retriever = GraphRetriever(store)
    active_graph = store.get_active_subgraph("2025-06-01")
    
    # Mention Supplier A and Plant Delhi
    query = "Is Supplier A experiencing delays delivering to Plant Delhi?"
    matched = retriever.identify_entities_in_query(query, active_graph)
    
    assert "Supplier A" in matched
    assert "Plant Delhi" in matched
    assert "Supplier C" not in matched

def test_multi_hop_traversal():
    store = get_preconfigured_graph()
    retriever = GraphRetriever(store)
    
    # 2025 graph snapshot
    g_2025 = store.get_active_subgraph("2025-06-01")
    matched = {"Supplier A"}
    
    paths = retriever.traverse_multi_hop(g_2025, matched, max_depth=3)
    
    # Assert we traverse: Supplier A -> Component X -> Product Y
    found_component_link = False
    found_product_link = False
    
    for path in paths:
        for u, rel, v, status, desc in path:
            if u == "Supplier A" and rel == "SUPPLIES" and v == "Component X":
                found_component_link = True
            if u == "Component X" and rel == "USED_IN" and v == "Product Y":
                found_product_link = True
                
    assert found_component_link
    assert found_product_link

def test_vector_retriever():
    retriever = DocumentVectorRetriever(MOCK_DOCUMENTS)
    
    # Query for Supplier A performance
    results = retriever.retrieve("Supplier A performance incident delay", top_k=2)
    
    assert len(results) > 0
    # The incident report should rank highly
    assert any("Incident" in doc["title"] or "Performance" in doc["content"] for doc in results)
