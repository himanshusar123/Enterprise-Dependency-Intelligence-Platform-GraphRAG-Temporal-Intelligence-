from typing import List, Dict, Any
from src.graph_store import TemporalGraphStore

# Raw documents simulating enterprise text sources
MOCK_DOCUMENTS = [
    {
        "id": "doc_contract_c101",
        "title": "Contract C-101 - Supplier A & Apex Corp",
        "content": """CONTRACT C-101 (Date: 2025-01-01)
Agreement between Apex Corp and Supplier A. Supplier A is contracted to supply Component X to Apex Corp. 
Delivery target is Plant Delhi. The contract duration is 3 years starting Jan 2025. 
Approved status is granted to Supplier A. Contract terms specify a penalty for late deliveries.""",
        "category": "Contract",
        "date": "2025-01-01"
    },
    {
        "id": "doc_product_spec_y",
        "title": "Product Y Specification Document",
        "content": """PRODUCT SPECIFICATION: PRODUCT Y (Date: 2025-02-15)
Product Y is a critical telecom communication unit developed by Apex Corp.
Assembly details: Product Y is exclusively manufactured at Plant Delhi.
Dependencies: Manufacturing requires two primary components: Component X and Component Z.
Sales: Customer Global Retail has signed an agreement to purchase 500 units of Product Y annually.""",
        "category": "Specification",
        "date": "2025-02-15"
    },
    {
        "id": "doc_incident_jan2026",
        "title": "Supplier A Incident Report - Jan 2026",
        "content": """SUPPLIER A PERFORMANCE INCIDENT (Date: 2026-01-12)
Supplier A has experienced an energy supply outage at their production hub.
Impact: Shipments of Component X to Plant Delhi are delayed by 4 weeks. 
Evaluation: Plant Delhi has reported a 30% reduction in Product Y manufacturing throughput. 
Status: Relationship flagged for review due to performance decline.""",
        "category": "Incident Report",
        "date": "2026-01-12"
    },
    {
        "id": "doc_suspension_aug2026",
        "title": "Contract C-101 Suspension Notice",
        "content": """CONTRACT C-101 SUSPENSION (Date: 2026-08-10)
Official notice from Apex Corp Procurement Division. Due to persistent delivery delays, quality degradation, 
and unresolved incidents documented between Jan 2026 and July 2026, Contract C-101 with Supplier A is 
hereby suspended immediately. All purchase orders for Component X from Supplier A are frozen.""",
        "category": "Contract Notice",
        "date": "2026-08-10"
    },
    {
        "id": "doc_contract_c102",
        "title": "Contract C-102 - Supplier C Onboarding",
        "content": """CONTRACT C-102 (Date: 2026-08-15)
Agreement between Apex Corp and Supplier C. Supplier C is approved as the replacement vendor for Component X,
delivering directly to Plant Delhi. Contract is initiated on August 15, 2026. 
Supplier C is designated as the primary active source for Component X to replace Supplier A.""",
        "category": "Contract",
        "date": "2026-08-15"
    },
    {
        "id": "doc_plant_delhi_summary",
        "title": "Plant Delhi Operations Manual",
        "content": """PLANT DELHI STATUS (Date: 2025-01-10)
Plant Delhi is Apex Corp's primary manufacturing facility in North India. 
The plant handles assembly for Product Y. Facilities require secure supply channels for Component X and Component Z.
Plant Director: Amit Sharma.""",
        "category": "Internal Documentation",
        "date": "2025-01-10"
    },
    {
        "id": "doc_contract_c103",
        "title": "Contract C-103 - Supplier B",
        "content": """CONTRACT C-103 (Date: 2025-01-05)
Agreement between Apex Corp and Supplier B. Supplier B is contracted to supply Component Z to Plant Delhi. 
Status: Active and compliant. Contract active through 2027.""",
        "category": "Contract",
        "date": "2025-01-05"
    }
]

def get_preconfigured_graph() -> TemporalGraphStore:
    """
    Build and return a pre-configured TemporalGraphStore reflecting the narrative:
    - 2025: Supplier A -> active, Contract C-101 active, supplies Component X.
    - Jan 2026: Incident, performance decline flagged.
    - Aug 2026: Supplier A suspended. Supplier C onboarded to replace Supplier A.
    """
    store = TemporalGraphStore()

    # --- 1. Add Entities ---
    # Suppliers
    store.add_entity("Supplier A", "Supplier", {"location": "Noida", "rating": 4.2})
    store.add_entity("Supplier B", "Supplier", {"location": "Mumbai", "rating": 4.8})
    store.add_entity("Supplier C", "Supplier", {"location": "Gurugram", "rating": 4.5})

    # Components
    store.add_entity("Component X", "Component", {"description": "Semiconductor microcontroller unit"})
    store.add_entity("Component Z", "Component", {"description": "RF Transceiver module"})

    # Products
    store.add_entity("Product Y", "Product", {"sku": "PROD-Y-TELE", "unit_price": 1200.00})

    # Plants
    store.add_entity("Plant Delhi", "Plant", {"region": "North", "capacity": 10000})

    # Contracts
    store.add_entity("Contract C-101", "Contract", {"value": 5000000})
    store.add_entity("Contract C-102", "Contract", {"value": 6000000})
    store.add_entity("Contract C-103", "Contract", {"value": 3000000})

    # Customers
    store.add_entity("Customer Global Retail", "Customer", {"market": "Enterprise Logistics"})

    # --- 2. Record Node Status Timelines ---
    # Supplier A status changes
    store.add_entity_status_change("Supplier A", "2025-01-01", "Active", "Approved Supplier")
    store.add_entity_status_change("Supplier A", "2026-01-12", "Active", "Performance decline - delayed deliveries")
    store.add_entity_status_change("Supplier A", "2026-08-10", "Suspended", "Contract suspended due to delivery breaches")

    # Supplier C status changes (not active until onboarded)
    store.add_entity_status_change("Supplier C", "2026-08-15", "Active", "Approved Supplier - onboarded as replacement")

    # Contract status changes
    store.add_entity_status_change("Contract C-101", "2025-01-01", "Active", "Agreement signed")
    store.add_entity_status_change("Contract C-101", "2026-08-10", "Suspended", "Suspension notice issued")
    
    store.add_entity_status_change("Contract C-102", "2026-08-15", "Active", "Replacement contract signed")

    # --- 3. Add Relationships & Timelines ---
    # Contract mappings
    store.add_relationship("Supplier A", "Contract C-101", "CONTRACTED_WITH")
    store.add_relationship_status_change("Supplier A", "Contract C-101", "CONTRACTED_WITH", "2025-01-01", "Active")
    store.add_relationship_status_change("Supplier A", "Contract C-101", "CONTRACTED_WITH", "2026-08-10", "Suspended")

    store.add_relationship("Supplier C", "Contract C-102", "CONTRACTED_WITH")
    store.add_relationship_status_change("Supplier C", "Contract C-102", "CONTRACTED_WITH", "2026-08-15", "Active")

    store.add_relationship("Supplier B", "Contract C-103", "CONTRACTED_WITH")
    store.add_relationship_status_change("Supplier B", "Contract C-103", "CONTRACTED_WITH", "2025-01-05", "Active")

    # Supply mappings
    store.add_relationship("Supplier A", "Component X", "SUPPLIES")
    store.add_relationship_status_change("Supplier A", "Component X", "SUPPLIES", "2025-01-01", "Active")
    store.add_relationship_status_change("Supplier A", "Component X", "SUPPLIES", "2026-08-10", "Suspended")

    store.add_relationship("Supplier C", "Component X", "SUPPLIES")
    store.add_relationship_status_change("Supplier C", "Component X", "SUPPLIES", "2026-08-15", "Active")

    store.add_relationship("Supplier B", "Component Z", "SUPPLIES")
    store.add_relationship_status_change("Supplier B", "Component Z", "SUPPLIES", "2025-01-05", "Active")

    # Dependency mappings
    store.add_relationship("Component X", "Product Y", "USED_IN")
    store.add_relationship_status_change("Component X", "Product Y", "USED_IN", "2025-02-15", "Active")

    store.add_relationship("Component Z", "Product Y", "USED_IN")
    store.add_relationship_status_change("Component Z", "Product Y", "USED_IN", "2025-02-15", "Active")

    # Manufacturing location
    store.add_relationship("Product Y", "Plant Delhi", "MANUFACTURED_AT")
    store.add_relationship_status_change("Product Y", "Plant Delhi", "MANUFACTURED_AT", "2025-02-15", "Active")

    # Customer purchase
    store.add_relationship("Product Y", "Customer Global Retail", "SOLD_TO")
    store.add_relationship_status_change("Product Y", "Customer Global Retail", "SOLD_TO", "2025-02-15", "Active")

    # Replacement association
    store.add_relationship("Supplier C", "Supplier A", "REPLACES")
    store.add_relationship_status_change("Supplier C", "Supplier A", "REPLACES", "2026-08-15", "Active")

    return store
