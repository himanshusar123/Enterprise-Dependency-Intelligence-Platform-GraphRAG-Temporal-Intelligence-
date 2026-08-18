import re
from typing import List, Dict, Any, Set, Tuple
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.graph_store import TemporalGraphStore

class GraphRetriever:
    def __init__(self, store: TemporalGraphStore):
        self.store = store

    def identify_entities_in_query(self, query: str, active_graph: nx.MultiDiGraph) -> Set[str]:
        """
        Identify which entities from the graph are mentioned in the query (case-insensitive).
        """
        matched_entities = set()
        query_lower = query.lower()
        
        # Sort nodes by length descending to match longer names first (e.g. "Plant Delhi" before "Delhi")
        sorted_nodes = sorted(active_graph.nodes(), key=len, reverse=True)
        
        for node in sorted_nodes:
            # Check for word boundary or direct inclusion
            # e.g., matching "Supplier A" in "Supplier A is disrupted"
            # Escaping in case entity names have special regex characters
            pattern = r'\b' + re.escape(node.lower()) + r'\b'
            if re.search(pattern, query_lower) or node.lower() in query_lower:
                matched_entities.add(node)
                
        return matched_entities

    def traverse_multi_hop(self, active_graph: nx.MultiDiGraph, start_nodes: Set[str], max_depth: int = 3) -> List[List[Tuple[str, str, str, str, str]]]:
        """
        Traverse the graph from start nodes up to max_depth hops.
        Collects paths of (source, relation_type, target, edge_status, edge_description).
        Supports traversing in both outgoing (downstream impact) and incoming (upstream dependency) directions.
        """
        paths = []
        visited_paths = set()

        def dfs(current_node: str, current_path: List[Tuple[str, str, str, str, str]], depth: int):
            if depth >= max_depth:
                return

            # 1. Outgoing edges (downstream)
            if active_graph.has_node(current_node):
                for _, neighbor, key, data in active_graph.out_edges(current_node, keys=True, data=True):
                    rel_type = data.get('relation_type', 'CONNECTED_TO')
                    status = data.get('status', 'Active')
                    desc = data.get('properties', {}).get('description', '')
                    
                    step = (current_node, rel_type, neighbor, status, desc)
                    path_key = tuple(current_path + [step])
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        new_path = current_path + [step]
                        paths.append(new_path)
                        dfs(neighbor, new_path, depth + 1)

            # 2. Incoming edges (upstream)
            if active_graph.has_node(current_node):
                for parent, _, key, data in active_graph.in_edges(current_node, keys=True, data=True):
                    rel_type = data.get('relation_type', 'CONNECTED_TO')
                    status = data.get('status', 'Active')
                    desc = data.get('properties', {}).get('description', '')
                    
                    # Store as parent -> rel_type -> current_node
                    step = (parent, f"INVERSE_{rel_type}", current_node, status, desc)
                    path_key = tuple(current_path + [step])
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        new_path = current_path + [step]
                        paths.append(new_path)
                        dfs(parent, new_path, depth + 1)

        for node in start_nodes:
            dfs(node, [], 0)

        # Sort paths by length so shorter, more direct paths appear first
        return sorted(paths, key=len)

    def format_paths_as_text(self, paths: List[List[Tuple[str, str, str, str, str]]], active_graph: nx.MultiDiGraph) -> str:
        """
        Format the traversed paths and node metadata into a structured text context.
        """
        if not paths:
            return "No matching relationships found in the active knowledge graph."

        lines = []
        lines.append("### Relevant Knowledge Graph Connections (Evidence Paths):")
        
        # Keep track of unique relationships described to avoid duplicate printouts
        seen_relations = set()
        
        # Describe paths
        for path in paths:
            path_str = " -> ".join([f"[{u}] --({rel})--> [{v}]" for u, rel, v, status, desc in path])
            if path_str not in seen_relations:
                seen_relations.add(path_str)
                lines.append(f"- Path: {path_str}")
                # Print details of the steps
                for u, rel, v, status, desc in path:
                    desc_str = f" ({desc})" if desc else ""
                    # lines.append(f"  * Relationship: {u} {rel} {v} | Status: {status}{desc_str}")

        # Collect all unique nodes involved in the paths to print their attributes
        involved_nodes = set()
        for path in paths:
            for u, _, v, _, _ in path:
                involved_nodes.add(u)
                involved_nodes.add(v)

        lines.append("\n### Involved Entity Profiles:")
        for node in involved_nodes:
            if active_graph.has_node(node):
                node_data = active_graph.nodes[node]
                entity_type = node_data.get('entity_type', 'Unknown')
                props = node_data.get('properties', {})
                status = node_data.get('status', 'Active')
                desc = node_data.get('status_description', '')
                
                props_str = ", ".join([f"{k}: {v}" for k, v in props.items() if k != 'extracted_by'])
                props_display = f" ({props_str})" if props_str else ""
                status_display = f" [Status: {status}" + (f" - {desc}]" if desc else "]")
                
                lines.append(f"- Entity: {node} ({entity_type}){props_display} {status_display}")

        return "\n".join(lines)


class DocumentVectorRetriever:
    """
    TF-IDF based semantic similarity retriever to index and query raw unstructured documents.
    Provides robust, dependency-free text search.
    """
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # Prepare corpus
        self.corpus = [f"Title: {doc['title']}\nContent: {doc['content']}" for doc in documents]
        if self.corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
        else:
            self.tfidf_matrix = None

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find top K documents similar to query.
        """
        if self.tfidf_matrix is None or not self.corpus:
            return []
            
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Sort in descending order of similarity
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            # Only return matches with score > 0.0 to prevent completely irrelevant retrievals
            if score > 0.0:
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
                
        return results


class HybridGraphRetriever:
    """
    Combines Knowledge Graph multi-hop traversal with Vector Document retrieval.
    """
    def __init__(self, store: TemporalGraphStore, documents: List[Dict[str, Any]]):
        self.store = store
        self.graph_retriever = GraphRetriever(store)
        self.vector_retriever = DocumentVectorRetriever(documents)

    def retrieve(self, query: str, as_of_date: str, max_depth: int = 3, top_k_docs: int = 3) -> Dict[str, Any]:
        # 1. Get the active subgraph as of the requested date
        active_graph = self.store.get_active_subgraph(as_of_date)
        
        # 2. Identify mentioned entities
        matched_entities = self.graph_retriever.identify_entities_in_query(query, active_graph)
        
        # 3. Perform multi-hop traversal from identified entities
        paths = []
        graph_context = ""
        if matched_entities:
            paths = self.graph_retriever.traverse_multi_hop(active_graph, matched_entities, max_depth)
            graph_context = self.graph_retriever.format_paths_as_text(paths, active_graph)
        else:
            graph_context = "No entities mentioned in the query were found in the active knowledge graph."

        # 4. Perform vector text search
        vector_docs = self.vector_retriever.retrieve(query, top_k_docs)
        
        # 5. Fuse context
        fused_context_parts = []
        if graph_context:
            fused_context_parts.append(graph_context)
            
        if vector_docs:
            doc_lines = ["\n### Relevant Supporting Text Segments (Vector Search):"]
            for doc in vector_docs:
                doc_lines.append(f"- Document: {doc['title']} (Score: {doc['score']:.2f})")
                doc_lines.append(f"  Content: {doc['content']}")
            fused_context_parts.append("\n".join(doc_lines))
            
        fused_context = "\n\n=======================\n\n".join(fused_context_parts)

        return {
            "query": query,
            "as_of_date": as_of_date,
            "matched_entities": list(matched_entities),
            "paths": paths,
            "vector_documents": vector_docs,
            "fused_context": fused_context
        }
