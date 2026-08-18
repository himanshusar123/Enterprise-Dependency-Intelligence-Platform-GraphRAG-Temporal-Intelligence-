import networkx as nx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class TemporalGraphStore:
    def __init__(self):
        # We use MultiDiGraph to support multiple directed edges of different relation types between same nodes
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity_id: str, entity_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Add or update an entity (node) in the knowledge graph.
        """
        properties = properties or {}
        if not self.graph.has_node(entity_id):
            self.graph.add_node(
                entity_id,
                entity_type=entity_type,
                properties=properties,
                timeline=[]
            )
        else:
            # Update properties
            self.graph.nodes[entity_id]['properties'].update(properties)

    def add_entity_status_change(self, entity_id: str, timestamp: str, status: str, description: str = "") -> None:
        """
        Record a status change in an entity's timeline.
        """
        if not self.graph.has_node(entity_id):
            raise ValueError(f"Entity '{entity_id}' does not exist.")
        
        timeline = self.graph.nodes[entity_id]['timeline']
        timeline.append({
            "timestamp": timestamp,
            "status": status,
            "description": description
        })
        # Sort timeline by timestamp
        self.graph.nodes[entity_id]['timeline'] = sorted(timeline, key=lambda x: x['timestamp'])

    def add_relationship(self, source: str, target: str, relation_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Add or update a relationship (edge) between two entities.
        """
        if not self.graph.has_node(source):
            raise ValueError(f"Source entity '{source}' does not exist.")
        if not self.graph.has_node(target):
            raise ValueError(f"Target entity '{target}' does not exist.")
        
        properties = properties or {}
        
        # Check if the edge already exists
        edge_key = f"{source}-{relation_type}-{target}"
        has_edge = False
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            if u == source and v == target and data.get('relation_type') == relation_type:
                # Update properties
                data['properties'].update(properties)
                has_edge = True
                break
                
        if not has_edge:
            self.graph.add_edge(
                source,
                target,
                key=edge_key,
                relation_type=relation_type,
                properties=properties,
                timeline=[]
            )

    def add_relationship_status_change(self, source: str, target: str, relation_type: str, timestamp: str, status: str, description: str = "") -> None:
        """
        Record a status change in a relationship's timeline.
        """
        edge_key = f"{source}-{relation_type}-{target}"
        if not self.graph.has_edge(source, target, key=edge_key):
            # Create the edge if it doesn't exist
            self.add_relationship(source, target, relation_type)
            
        edge_data = self.graph.edges[source, target, edge_key]
        timeline = edge_data['timeline']
        timeline.append({
            "timestamp": timestamp,
            "status": status,
            "description": description
        })
        # Sort timeline by timestamp
        edge_data['timeline'] = sorted(timeline, key=lambda x: x['timestamp'])

    def _get_status_at(self, timeline: List[Dict[str, Any]], as_of_date: str, default_status: str = "Active") -> tuple[str, str]:
        """
        Helper to find the state of an item at a specific ISO timestamp ("YYYY-MM-DD").
        Returns (status, description).
        """
        if not timeline:
            return default_status, "Initial state"
            
        current_status = default_status
        current_desc = "Initial state"
        
        # Find the latest state change that is <= as_of_date
        for event in timeline:
            if event['timestamp'] <= as_of_date:
                current_status = event['status']
                current_desc = event['description']
            else:
                break
                
        return current_status, current_desc

    def get_active_subgraph(self, as_of_date: str) -> nx.MultiDiGraph:
        """
        Generate a snapshot of the graph representing active entities and relations as of a target date.
        """
        active_subgraph = nx.MultiDiGraph()
        
        # 1. Filter and add active nodes
        for node, data in self.graph.nodes(data=True):
            status, desc = self._get_status_at(data['timeline'], as_of_date)
            # If the node's first timeline event is after the target date, it shouldn't exist yet
            first_event_date = data['timeline'][0]['timestamp'] if data['timeline'] else None
            
            if first_event_date and first_event_date > as_of_date:
                continue # Node doesn't exist yet
                
            if status not in ["Inactive", "Suspended", "Terminated"]:
                active_subgraph.add_node(
                    node,
                    entity_type=data['entity_type'],
                    properties=data['properties'],
                    status=status,
                    status_description=desc
                )

        # 2. Filter and add active edges between active nodes
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            if u in active_subgraph and v in active_subgraph:
                status, desc = self._get_status_at(data['timeline'], as_of_date)
                first_event_date = data['timeline'][0]['timestamp'] if data['timeline'] else None
                
                if first_event_date and first_event_date > as_of_date:
                    continue # Relationship doesn't exist yet
                    
                if status not in ["Inactive", "Suspended", "Terminated"]:
                    active_subgraph.add_edge(
                        u, v,
                        key=key,
                        relation_type=data['relation_type'],
                        properties=data['properties'],
                        status=status,
                        status_description=desc
                    )
                    
        return active_subgraph

    def get_entity_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve history timeline for a node.
        """
        if not self.graph.has_node(entity_id):
            return []
        return self.graph.nodes[entity_id]['timeline']

    def get_relationship_history(self, source: str, target: str, relation_type: str) -> List[Dict[str, Any]]:
        """
        Retrieve history timeline for an edge.
        """
        edge_key = f"{source}-{relation_type}-{target}"
        if not self.graph.has_edge(source, target, key=edge_key):
            return []
        return self.graph.edges[source, target, edge_key]['timeline']

    def to_json(self) -> str:
        """
        Serialize the entire temporal graph to a JSON string.
        """
        nodes_list = []
        for node, data in self.graph.nodes(data=True):
            nodes_list.append({
                "id": node,
                "entity_type": data["entity_type"],
                "properties": data["properties"],
                "timeline": data["timeline"]
            })
            
        edges_list = []
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "relation_type": data["relation_type"],
                "properties": data["properties"],
                "timeline": data["timeline"]
            })
            
        return json.dumps({"nodes": nodes_list, "edges": edges_list}, indent=2)

    def load_from_json(self, json_str: str) -> None:
        """
        Load graph store from serialized JSON string.
        """
        self.graph.clear()
        data = json.loads(json_str)
        
        for node in data.get("nodes", []):
            self.graph.add_node(
                node["id"],
                entity_type=node["entity_type"],
                properties=node["properties"],
                timeline=node["timeline"]
            )
            
        for edge in data.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            rel_type = edge["relation_type"]
            edge_key = f"{source}-{rel_type}-{target}"
            self.graph.add_edge(
                source,
                target,
                key=edge_key,
                relation_type=rel_type,
                properties=edge["properties"],
                timeline=edge["timeline"]
            )
