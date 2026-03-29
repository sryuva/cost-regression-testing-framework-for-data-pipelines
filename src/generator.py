"""
Hypothesis Generator: produces diverse solutions, now with hotspot-aware targeted prompts.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from litellm import completion
import json


class Hypothesis(BaseModel):
    approach: str
    code: str
    explanation: str


class HypothesisGenerator:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def _build_prompt(self, problem: dict, count: int, hotspots: Optional[List[Dict[str, Any]]] = None, guardrails: Optional[List[str]] = None) -> str:
        """Build the generation prompt. If hotspots are provided, make it surgical."""
        base = f"""
Given the following problem, generate {count} fundamentally different approaches to solve it.
Provide valid, self-contained Python code for each approach.
The code MUST define a function called 'solve(input_val)'.

Problem:
{json.dumps(problem, indent=2)}
"""
        # Targeted optimization: feed hotspot data into the prompt
        if hotspots:
            hotspot_text = "\n".join(
                [f"  Line {h['line']}: {h['time_us']}μs total ({h['hits']} hits)" for h in hotspots]
            )
            base += f"""

PROFILING DATA — Hotspots detected in the current best solution:
{hotspot_text}

Focus your optimization ONLY on these expensive lines.
Do NOT rewrite everything blindly. Surgical improvements only.
"""

        if guardrails:
            base += "\\nSTRICT GUARDRAILS (Must not violate):\\n"
            for g in guardrails:
                base += f"- {g}\\n"

        base += """
Output format:
{
    "hypotheses": [
        {
            "approach": "name",
            "code": "python code...",
            "explanation": "..."
        },
        ...
    ]
}
"""
        return base

    def generate(self, problem: dict, count: int = 5, hotspots: Optional[List[Dict[str, Any]]] = None, guardrails: Optional[List[str]] = None) -> List[Hypothesis]:
        """
        Generate diverse solutions. If hotspots are provided, generate targeted optimizations instead.
        """
        prompt = self._build_prompt(problem, count, hotspots, guardrails)

        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        return [Hypothesis(**h) for h in data.get("hypotheses", [])]
