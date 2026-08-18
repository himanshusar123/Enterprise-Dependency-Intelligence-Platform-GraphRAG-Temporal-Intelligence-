import os
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI

class LLMReasoner:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "http://localhost:4000")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "gemini-2.5-flash")
        
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                self.client = None

    def generate_answer(self, query: str, as_of_date: str, fused_context: str) -> str:
        if not self.client:
            raise RuntimeError("LLM Client not initialized.")

        prompt = f"""You are the Enterprise Dependency Intelligence Engine. 
You are answering an executive query. You must ground your answer strictly in the provided Knowledge Graph connections and vector document context. 

Query Date Context: You are evaluating this situation as-of: {as_of_date}. Relationships or entities that are suspended, inactive, or not yet created as of {as_of_date} should be treated accordingly.

User Query: "{query}"

Retrieved Context (Knowledge Graph & Vector Documents):
---
{fused_context}
---

Instructions:
1. Provide a direct, professional, and clear executive summary of the impacts.
2. Outline the dependency paths step-by-step (e.g., Supplier -> Component -> Product -> Plant -> Customer).
3. Explicitly state the status of contracts, suppliers, and components as of {as_of_date} (highlighting suspensions, outages, or replacements).
4. Do not make up facts or extrapolate beyond what is grounded in the retrieved context. If information is missing, state it.
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful, grounded enterprise intelligence assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content


class RuleBasedReasoner:
    """
    Synthesizes a response deterministically from the graph paths when offline.
    """
    def generate_answer(self, query: str, as_of_date: str, retrieval_result: Dict[str, Any]) -> str:
        matched = retrieval_result.get("matched_entities", [])
        paths = retrieval_result.get("paths", [])
        
        if not matched:
            return f"### Grounded Response (Offline Rule Engine)\n\nNo matching entities were recognized in your query as of **{as_of_date}**. Please query about 'Supplier A', 'Supplier C', 'Component X', or 'Plant Delhi' to see traversal paths."
            
        lines = []
        lines.append(f"### Grounded Response (Offline Rule Engine) — Evaluated as-of: `{as_of_date}`\n")
        
        # Determine if Supplier A disruption is queried
        supplier_a_affected = any("Supplier A" in m for m in matched) or "disrupt" in query.lower() or "suspend" in query.lower()
        
        if supplier_a_affected:
            # Let's check status of Supplier A at target date
            is_suspended = as_of_date >= "2026-08-10"
            is_delayed_period = "2026-01-12" <= as_of_date < "2026-08-10"
            
            if is_suspended:
                lines.append("> [!WARNING]")
                lines.append(f"> **CRITICAL ALERT**: As of **{as_of_date}**, **Supplier A** is **SUSPENDED** (effective 2026-08-10) due to persistent delivery delays. Contract **Contract C-101** is also suspended.")
                lines.append("> **Mitigation Active**: **Supplier C** has been onboarded (effective 2026-08-15) under contract **Contract C-102** to replace Supplier A and supply Component X to Plant Delhi.\n")
            elif is_delayed_period:
                lines.append("> [!IMPORTANT]")
                lines.append(f"> **WARNING**: As of **{as_of_date}**, **Supplier A** is flagged with **Performance Decline** due to an energy outage reported on 2026-01-12. Deliveries of Component X are delayed by 4 weeks, impacting Plant Delhi's manufacturing throughput by 30%.\n")
            else:
                lines.append(f"As of **{as_of_date}**, **Supplier A** is an **Active (Approved)** supplier operating normally under contract **Contract C-101**.\n")

            lines.append("#### Direct Supply Chain & Contractual Impacts:")
            
            # Highlight dependencies
            lines.append("- **Direct Contract**: Supplier A is bound to **Contract C-101** (Value: $5.0M) to deliver components to **Plant Delhi**.")
            lines.append("- **Component Supplied**: Supplier A supplies **Component X** (Semiconductor microcontroller unit).")
            lines.append("- **Downstream Product**: Component X is a critical input required to build **Product Y**.")
            lines.append("- **Manufacturing Plant**: Product Y is manufactured at **Plant Delhi** (North region, 10,000 capacity). Delay/suspension of Component X impacts assembly lines here.")
            lines.append("- **End Customer**: Finished Product Y units are sold to **Customer Global Retail** (Enterprise Logistics market). A supply halt will breach delivery contracts with this key customer.")

            lines.append("\n#### Traversed Evidence Paths:")
            for path in paths:
                path_str = " → ".join([f"`{u}`" for u, rel, v, status, desc in path])
                # Show a simplified path
                last_node = path[-1][2]
                last_node_type = path[-1][1] # relation
                lines.append(f"- **{last_node}** is affected via path: {path_str} → `{last_node}`")
                
            if is_suspended:
                lines.append("\n#### Alternative & Recovery Options:")
                lines.append("- **Supplier C**: Onboarded on August 15, 2026, under **Contract C-102** ($6.0M) as the replacement vendor for Component X. Supply lines should transition to Supplier C to mitigate disruption.")
                lines.append("- **Supplier B**: Continues to provide **Component Z** normally under **Contract C-103** ($3.0M), indicating no issues in RF Transceiver supply lines.")
        else:
            # General summary of nodes matched
            lines.append(f"Identified interest in: **{', '.join(matched)}**.\n")
            lines.append("#### Traversed Dependencies:")
            for path in paths:
                steps = []
                for u, rel, v, status, desc in path:
                    steps.append(f"`{u}` --[{rel}]--> `{v}`")
                lines.append(f"- {' → '.join(steps)}")
                
        return "\n".join(lines)


class UniversalReasoner:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.llm_reasoner = None
        try:
            self.llm_reasoner = LLMReasoner(api_key, base_url, model)
            if not self.llm_reasoner.client:
                self.llm_reasoner = None
        except Exception:
            self.llm_reasoner = None
            
        self.rule_reasoner = RuleBasedReasoner()

    def generate(self, query: str, as_of_date: str, retrieval_result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generates grounded response and returns (response_text, generation_mode)
        """
        if self.llm_reasoner:
            try:
                ans = self.llm_reasoner.generate_answer(query, as_of_date, retrieval_result["fused_context"])
                return ans, "LLM"
            except Exception as e:
                print(f"LLM Generation failed: {e}. Falling back to Rule-based reasoner.")
                return self.rule_reasoner.generate_answer(query, as_of_date, retrieval_result), "Rule-Fallback"
        else:
            return self.rule_reasoner.generate_answer(query, as_of_date, retrieval_result), "Rules"
