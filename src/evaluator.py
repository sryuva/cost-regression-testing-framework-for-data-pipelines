from pydantic import BaseModel
from typing import Dict, Any, Optional

class EvaluationScore(BaseModel):
    is_valid: bool
    compute_cost: float  # GB-seconds (lower is better)
    feedback: str = ""

class Evaluator:
    def evaluate(self, result: dict, runtime: float, memory_mb: float, constraints: Optional[Dict[str, Any]] = None) -> EvaluationScore:
        # STEP 1: Hard Filters
        if not result.get("passed", False):
            return EvaluationScore(is_valid=False, compute_cost=float("inf"), feedback="FAILED: Incorrect output")

        if constraints:
            if "max_latency" in constraints and runtime > constraints["max_latency"]:
                return EvaluationScore(is_valid=False, compute_cost=float("inf"), 
                                     feedback=f"FAILED: latency {runtime:.4f}s > {constraints['max_latency']}s")

            if "max_memory" in constraints and memory_mb > constraints["max_memory"]:
                return EvaluationScore(is_valid=False, compute_cost=float("inf"), 
                                     feedback=f"FAILED: memory {memory_mb:.1f}MB > {constraints['max_memory']}MB")

        # STEP 2: Optimize ONE objective (Compute Cost in GB-seconds)
        # Cost = Runtime (s) * Memory (GB)
        compute_cost = runtime * (max(memory_mb, 1.0) / 1024.0)
        
        return EvaluationScore(
            is_valid=True,
            compute_cost=compute_cost,
            feedback=f"PASSED: Cost {compute_cost:.6f} GB-s ({runtime:.3f}s, {memory_mb:.1f}MB)"
        )
