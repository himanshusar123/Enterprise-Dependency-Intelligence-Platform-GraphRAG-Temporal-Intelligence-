import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import os
import json
from datetime import datetime
from src.mock_data import get_preconfigured_graph, MOCK_DOCUMENTS
from src.extractor import UniversalExtractor
from src.retriever import HybridGraphRetriever
from src.reasoner import UniversalReasoner

# --- 1. Streamlit Page Configuration ---
st.set_page_config(
    page_title="Enterprise GraphRAG & Temporal Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS Styles ---
st.markdown("""
<style>
    /* Theme overrides and custom styling */
    .main {
        background-color: #0f111a;
        color: #e6edf3;
    }
    .stAppHeader {
        background-color: #0f111a;
    }
    div[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    /* Premium card containers */
    .glass-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
    }
    .badge-supplier { background-color: #1f77b4; color: white; }
    .badge-component { background-color: #ff7f0e; color: white; }
    .badge-product { background-color: #2ca02c; color: white; }
    .badge-plant { background-color: #d62728; color: white; }
    .badge-contract { background-color: #bcbd22; color: black; }
    .badge-customer { background-color: #9467bd; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 3. Session State Initialization ---
if "graph_store" not in st.session_state:
    st.session_state.graph_store = get_preconfigured_graph()
if "documents" not in st.session_state:
    st.session_state.documents = MOCK_DOCUMENTS
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if "base_url" not in st.session_state:
    st.session_state.base_url = os.environ.get("ANTHROPIC_BASE_URL", "http://localhost:4000")
if "model" not in st.session_state:
    st.session_state.model = os.environ.get("ANTHROPIC_MODEL", "gemini-2.5-flash")

# --- 4. Sidebar Controls ---
st.sidebar.image("https://img.icons8.com/nolan/96/network.png", width=64)
st.sidebar.title("Dependency Intel")
st.sidebar.caption("GraphRAG & Temporal Intelligence")

st.sidebar.markdown("---")

# Presets dates mapping to timeline events
st.sidebar.subheader("📅 Target Timeline Date")

# Convert strings to dates for display
dates = ["2025-06-01", "2026-03-01", "2026-08-18"]
date_descriptions = {
    "2025-06-01": "Approved & Normal (2025)",
    "2026-03-01": "Outage & Delay Flagged (Jan 2026)",
    "2026-08-18": "Supplier A Suspended & Supplier C Active (Aug 2026)"
}

selected_date_str = st.sidebar.select_slider(
    "Evaluate state as-of:",
    options=dates,
    value="2026-08-18",
    format_func=lambda x: f"{x} ({date_descriptions[x]})"
)

st.sidebar.info(f"📍 **Evaluating topology as-of**: `{selected_date_str}`")

st.sidebar.markdown("---")

# LLM Config
st.sidebar.subheader("⚙️ LLM Configuration")
with st.sidebar.expander("API & Endpoint Settings"):
    api_key_input = st.text_input("API Key (Google/LiteLLM)", value=st.session_state.api_key, type="password")
    base_url_input = st.text_input("Base URL", value=st.session_state.base_url)
    model_input = st.text_input("Model Name", value=st.session_state.model)
    
    if st.button("Save Settings"):
        st.session_state.api_key = api_key_input
        st.session_state.base_url = base_url_input
        st.session_state.model = model_input
        st.success("Configuration updated!")

st.sidebar.caption("💡 If no API key is specified, the system automatically falls back to an offline determinisic rules engine that computes correct grounded answers and traces paths locally.")

# Instantiate core engines dynamically
extractor = UniversalExtractor(st.session_state.api_key, st.session_state.base_url, st.session_state.model)
retriever = HybridGraphRetriever(st.session_state.graph_store, st.session_state.documents)
reasoner = UniversalReasoner(st.session_state.api_key, st.session_state.base_url, st.session_state.model)

# --- 5. Main Page Layout ---
st.title("🌐 Enterprise Dependency Intelligence Platform")
st.markdown("##### Temporal GraphRAG for Supply Chain Risk & Impact Analysis")

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Ask Assistant (GraphRAG Query)", 
    "🗺️ Interactive Dependency Map", 
    "🕰️ Temporal Change Log Inspector", 
    "📥 Ingest New Documents"
])

# --- TAB 1: ASK ASSISTANT ---
with tab1:
    st.markdown("### Query the Dependency Knowledge Graph")
    st.write("Pose complex relationship, multi-hop, and impact-assessment questions to the enterprise repository.")
    
    # Preset queries
    st.markdown("**Example Queries:**")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        q1_btn = st.button("🚨 Supplier A Disruption Impact Summary")
    with col_q2:
        q2_btn = st.button("🔄 Alternative Suppliers for Component X")
        
    query_input = ""
    if q1_btn:
        query_input = "Supplier A is facing disruption. Which products, plants, customers and contracts are impacted, and what alternatives exist?"
    elif q2_btn:
        query_input = "What components are needed for Product Y, which suppliers provide them, and are there any active contract replacements?"
        
    query = st.text_input("Enter your query:", value=query_input, placeholder="Type your dependency question here...")
    
    if st.button("Run GraphRAG Query", type="primary"):
        if query:
            with st.spinner("Executing retrieval & multi-hop reasoning..."):
                # 1. Retrieve Graph + Vector context
                retrieval_result = retriever.retrieve(query, selected_date_str)
                
                # 2. Reason and Synthesize
                answer_text, mode = reasoner.generate(query, selected_date_str, retrieval_result)
                
                # 3. Render Answer
                st.markdown("#### Grounded Answer")
                st.markdown(f"<div class='glass-card'>{answer_text}</div>", unsafe_allow_html=True)
                
                # Render metadata mode
                st.caption(f"🤖 Answer generated via: **{mode} Mode**")
                
                # Show explicit evidence paths
                if retrieval_result["paths"]:
                    st.markdown("#### Retrieved Evidence Chain (Graph Traversal Paths):")
                    for path in retrieval_result["paths"]:
                        path_elements = []
                        for u, rel, v, status, desc in path:
                            # Color coding paths
                            path_elements.append(f"`{u}` ➔ `[{rel}]` ➔ `{v}`")
                        st.markdown(f"🧬 " + " ➔ ".join(path_elements))
                else:
                    st.info("No explicit dependency paths found for this entity query in the graph store.")
                
                # Expandable debug window
                with st.expander("🛠️ View Fused Search Context (Graph Chunks + Vector Chunks)"):
                    st.code(retrieval_result["fused_context"], language="markdown")
        else:
            st.warning("Please enter or select a query.")

# --- TAB 2: INTERACTIVE DEPENDENCY MAP ---
with tab2:
    st.markdown("### Interactive Dependency Graph")
    st.write(f"This graph represents all active entities and dependencies as of **{selected_date_str}**. Inactive, suspended, or not-yet-created entities/relationships are excluded from this snapshot.")
    
    # Generate active graph snapshot
    active_graph = st.session_state.graph_store.get_active_subgraph(selected_date_str)
    
    if len(active_graph.nodes()) == 0:
        st.info("No active entities in the graph as of this date.")
    else:
        # Create positions using a layout
        pos = nx.spring_layout(active_graph, k=1.2, seed=42)
        
        # Color mapping for entity types
        color_map = {
            "Supplier": "#1f77b4",   # Blue
            "Component": "#ff7f0e",  # Orange
            "Product": "#2ca02c",    # Green
            "Plant": "#d62728",      # Red
            "Contract": "#bcbd22",   # Olive
            "Customer": "#9467bd"    # Purple
        }
        
        # Draw edges
        edge_traces = []
        
        # We draw individual lines so each can have hover text
        for u, v, key, data in active_graph.edges(keys=True, data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            rel_type = data.get("relation_type", "CONNECTED_TO")
            status = data.get("status", "Active")
            desc = data.get("properties", {}).get("description", "")
            
            # Draw line
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=1.5, color='#888' if status == "Active" else '#d62728'),
                hoverinfo='text',
                text=f"{u} ➔ {rel_type} ➔ {v}<br>Status: {status}<br>{desc}",
                mode='lines'
            )
            edge_traces.append(edge_trace)
            
        # Draw nodes
        node_x = []
        node_y = []
        node_color = []
        node_text = []
        node_size = []
        
        for node in active_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = active_graph.nodes[node]
            ent_type = node_data.get("entity_type", "Unknown")
            status = node_data.get("status", "Active")
            desc = node_data.get("status_description", "")
            props = node_data.get("properties", {})
            
            node_color.append(color_map.get(ent_type, "#7f7f7f"))
            
            props_str = "<br>".join([f"• {k}: {v}" for k, v in props.items() if k != 'extracted_by'])
            node_text.append(f"<b>{node}</b> ({ent_type})<br>Status: {status}<br>{desc}<br>{props_str}")
            
            # Nodes are sized by their degree
            node_size.append(25 + active_graph.degree(node) * 5)
            
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[str(node) for node in active_graph.nodes()],
            textposition="top center",
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(
                showscale=False,
                color=node_color,
                size=node_size,
                line=dict(width=2, color='#fff')
            )
        )
        
        # Draw edge mid-points for relation labels on hover
        mid_x = []
        mid_y = []
        mid_text = []
        for u, v, key, data in active_graph.edges(keys=True, data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            mid_x.append((x0 + x1) / 2.0)
            mid_y.append((y0 + y1) / 2.0)
            mid_text.append(f"Relation: {data.get('relation_type')} ({data.get('status')})")
            
        mid_trace = go.Scatter(
            x=mid_x, y=mid_y,
            mode='markers',
            hoverinfo='text',
            text=mid_text,
            marker=dict(
                size=8,
                color='rgba(255, 255, 255, 0.4)',
                line=dict(width=1, color='#888')
            )
        )
        
        # Build Figure
        fig = go.Figure(
            data=edge_traces + [mid_trace, node_trace],
            layout=go.Layout(
                title=dict(text='Enterprise Dependency Topology Plot', font=dict(color='#58a6ff')),
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='#0f111a',
                paper_bgcolor='#0f111a',
                height=650
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Legend guide
        st.markdown("##### Node Legend:")
        legend_cols = st.columns(6)
        types_list = ["Supplier", "Component", "Product", "Plant", "Contract", "Customer"]
        for i, t in enumerate(types_list):
            with legend_cols[i]:
                st.markdown(f"<span class='badge' style='background-color:{color_map[t]}; color:{'black' if t=='Contract' else 'white'}'>{t}</span>", unsafe_allow_html=True)

# --- TAB 3: TEMPORAL LOG INSPECTOR ---
with tab3:
    st.markdown("### Temporal Change Log Inspector")
    st.write("Inspect the changes that have occurred over time for individual entities or relationships.")
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        # Choose node
        all_nodes = sorted(list(st.session_state.graph_store.graph.nodes()))
        selected_node = st.selectbox("Select an Entity to inspect history:", all_nodes, index=0)
        
        history = st.session_state.graph_store.get_entity_history(selected_node)
        if history:
            st.markdown(f"#### Timeline of status changes for `{selected_node}`")
            # Render a custom timeline list
            for idx, event in enumerate(history):
                # Using a bullet with alert styles
                color = "green" if event['status'] == "Active" else "orange" if event['status'] == "Suspended" else "red"
                st.markdown(f"📆 **{event['timestamp']}** — Status: <span style='color:{color}; font-weight:bold;'>{event['status']}</span> — *{event['description']}*", unsafe_allow_html=True)
        else:
            st.info(f"No status events recorded for node '{selected_node}'. It operates in default Active state.")

    with col_sel2:
        # Choose edge
        all_edges = []
        for u, v, key, data in st.session_state.graph_store.graph.edges(keys=True, data=True):
            all_edges.append((u, v, data.get("relation_type", "CONNECTED_TO")))
            
        all_edges = sorted(list(set(all_edges)))
        selected_edge_idx = st.selectbox(
            "Select a Relationship to inspect history:", 
            range(len(all_edges)),
            format_func=lambda i: f"{all_edges[i][0]} --[{all_edges[i][2]}]--> {all_edges[i][1]}"
        )
        
        if all_edges:
            u, v, rel_type = all_edges[selected_edge_idx]
            edge_history = st.session_state.graph_store.get_relationship_history(u, v, rel_type)
            if edge_history:
                st.markdown(f"#### Timeline of changes for `{u} ➔ {rel_type} ➔ {v}`")
                for event in edge_history:
                    color = "green" if event['status'] == "Active" else "red"
                    st.markdown(f"📆 **{event['timestamp']}** — Status: <span style='color:{color}; font-weight:bold;'>{event['status']}</span> — *{event['description']}*", unsafe_allow_html=True)
            else:
                st.info(f"No explicit status timeline events recorded for relationship.")

# --- TAB 4: DOCUMENT INGEST & EXTRACTION ---
with tab4:
    st.markdown("### Document Ingest & Dynamic Knowledge Graph Extraction")
    st.write("Upload or paste unstructured text documents (e.g. contracts, incident sheets). The extractor parses them, extracts nodes and relationships, and merges them into the active graph.")
    
    doc_title = st.text_input("Document Title:", placeholder="e.g. Plant Chennai Fire Incident Report")
    doc_date = st.date_input("Document Date:", value=datetime.now())
    doc_date_str = doc_date.strftime("%Y-%m-%d")
    
    doc_content = st.text_area("Document Content (Paste Text):", height=200, placeholder="Paste contract text or reports here...")
    
    if st.button("Process & Integrate Document", type="primary"):
        if doc_title and doc_content:
            with st.spinner("Extracting entities & relationships..."):
                # Run extractor
                extraction_result, mode_used = extractor.extract(doc_content, doc_date_str)
                
                # Show results extracted
                st.success(f"Successfully processed document using **{mode_used} Extractor**!")
                
                # Merge into graph
                extractor.merge_into_store(st.session_state.graph_store, extraction_result)
                
                # Append to raw documents list
                new_doc = {
                    "id": f"doc_{int(datetime.now().timestamp())}",
                    "title": doc_title,
                    "content": doc_content,
                    "category": "User Upload",
                    "date": doc_date_str
                }
                st.session_state.documents.append(new_doc)
                
                # Re-index Document Vector retriever
                retriever.vector_retriever = retriever.vector_retriever.__class__(st.session_state.documents)
                
                # Render Extracted details
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.markdown("##### Extracted Entities:")
                    for ent in extraction_result.entities:
                        st.markdown(f"- **{ent.id}** ({ent.entity_type}) [Status: {ent.status}]")
                with col_e2:
                    st.markdown("##### Extracted Relationships:")
                    for rel in extraction_result.relationships:
                        st.markdown(f"- `{rel.source}` ➔ `{rel.relation_type}` ➔ `{rel.target}` (Effective: {rel.timestamp})")
                        
                st.balloons()
        else:
            st.warning("Please provide both a title and content for the document.")
            
    # List current document list
    st.markdown("---")
    st.markdown("#### Currently Indexed Enterprise Documents")
    for d in st.session_state.documents:
        with st.expander(f"📄 {d['title']} ({d['date']})"):
            st.write(d['content'])
