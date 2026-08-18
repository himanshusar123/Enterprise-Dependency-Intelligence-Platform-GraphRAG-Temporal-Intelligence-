# 🌐 Enterprise Dependency Intelligence Platform (GraphRAG & Temporal Intelligence)

Welcome to **Week 7 – Day 2** of the Enterprise AI Training. This repository contains the complete implementation for the **Enterprise Dependency Intelligence Platform**, showcasing how to move beyond traditional Vector RAG to structured **GraphRAG & Temporal Intelligence**.

---

## 📖 The Business Scenario
A manufacturing enterprise handles a complex supply chain with dependencies across suppliers, contracts, components, products, plants, and end-customers:
1. **Supplier A** supplies **Component X** (Semiconductor Microcontroller) to **Plant Delhi** under **Contract C-101**.
2. **Component X** and **Component Z** are assembled into **Product Y**.
3. **Product Y** is manufactured at **Plant Delhi** and sold to **Customer Global Retail**.
4. **Supplier B** supplies **Component Z** to **Plant Delhi** under **Contract C-103**.

### The Temporal Narrative:
* **2025-01-01**: Contracts signed, operations are normal. Supplier A and Contract C-101 are active and approved.
* **2026-01-12**: Supplier A suffers an energy outage, resulting in major component delays. Operations throughput at Plant Delhi drops by 30%.
* **2026-08-10**: Apex Corp Procurement suspends Contract C-101 with Supplier A.
* **2026-08-15**: **Supplier C** is onboarded as a replacement vendor under **Contract C-102** to deliver Component X to Plant Delhi.

### The Question:
> **"A critical supplier is facing disruption. Which products, plants, customers and contracts are impacted, what alternatives exist, and how has the supplier relationship changed over time?"**

Traditional vector search would return isolated document fragments. This platform uses **GraphRAG** to trace the entire dependency chain and resolve the answer dynamically based on the temporal snapshot.

---

## 🏗️ Core Architecture

```text
                 Enterprise Documents
                         │
                         ▼
                 Entity Extraction (UniversalExtractor: LLM / Rules Fallback)
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
       Entities                    Relationships
          │                             │
          └──────────────┬──────────────┘
                         ▼
                 Temporal Graph Store (NetworkX MultiDiGraph)
                         │
                         │
User Query ──────────────┤
                         ▼
               Query Understanding (Entity Recognition)
                         │
                Graph Traversal (Multi-Hop Paths: Upstream & Downstream)
                         │
                Vector Retrieval (Document Search: TF-IDF fallback)
                         │
               Hybrid Fusion & Reranking
                         │
                  Evidence Context (Grounding Context)
                         │
                 UniversalReasoner (LLM / Rule-Based Fallback)
                         │
               Grounded Final Answer + Traversed Paths
```

---

## 📂 Project Structure

```text
enterprise-dependency-intelligence-platform/
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── graph_store.py      # NetworkX multi-directional graph store with temporal timeline filtering
│   ├── extractor.py        # LLM Entity Extractor with robust local Regex/Rule fallback parser
│   ├── retriever.py        # Entity matching, Multi-hop traversal, TF-IDF vector index, and hybrid fusion
│   ├── reasoner.py         # Grounded response generator with local offline templating fallback
│   └── mock_data.py        # Default mock documents and pre-configured temporal graph setup
├── app.py                  # Streamlit Interactive Web Dashboard
└── tests/
    ├── test_graph_store.py # Tests for temporal graph snapshot views
    └── test_retriever.py   # Tests for entity linking, BFS/DFS traversal, and document scoring
```

---

## ⚙️ Key Technical Features

1. **Temporal Subgraph View**:
   The `TemporalGraphStore` records historical status timelines for nodes and edges. When a query is run, the engine compiles an active subgraph **as-of** a specific historical date (e.g. 2025 vs 2026), filtering out suspended, deactivated, or not-yet-created links.
2. **Multi-Hop Traversal**:
   Instead of calculating text similarity, the retriever traverses relationships up to $N$ hops to trace downstream impact (e.g. *Supplier A ➔ Component X ➔ Product Y ➔ Plant Delhi ➔ Customer Global Retail*) and gathers profile metadata.
3. **Hybrid Search Fusion**:
   Combines semantic text chunks with explicit structured graph paths and injects them as a single grounded context into the reasoner prompt.
4. **Self-Contained Rule Fallbacks**:
   To ensure 100% reliable local operation (offline or without API keys), the Extractor and Reasoner implement deterministic fallback systems that parse and synthesize responses locally.

---

## 🚀 How to Run

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard
Start the interactive Streamlit interface:
```bash
streamlit run app.py
```

### 3. Run Unit Tests
Validate the temporal calculations, path traversals, and retrieval similarity:
```bash
python -m pytest tests/
```

---

## 🧬 Test Drive Queries to Try in the UI

* **Test query 1**: 
  > *"Supplier A is experiencing disruption. Which products, plants, and contracts are affected, and how has the relationship changed over time?"*
  * **As-of 2025**: The system will trace the active path and state that Supplier A is approved and supplying normally under Contract C-101.
  * **As-of Jan 2026**: The system will flag warnings of delivery delays (30% plant capacity drop) due to energy outages.
  * **As-of Aug 2026**: The system will trigger a critical alert stating Supplier A is **SUSPENDED**, contract C-101 is suspended, and **Supplier C** has been onboarded under contract C-102 as a replacement.

* **Test query 2**:
  > *"Which components does Product Y depend on, and who are their suppliers?"*
  * Shows multi-hop traversal in reverse (Product Y ➔ Component X ➔ Supplier A/C and Component Z ➔ Supplier B).
