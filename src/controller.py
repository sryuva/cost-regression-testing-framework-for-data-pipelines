"""
Iteration Controller: the core research loop.
Now with profiling-guided refinement, real input support, constraint passing, and diff output.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from litellm import completion
import json
import os

from src.parser import ProblemParser, ParsedProblem
from src.generator import HypothesisGenerator, Hypothesis
from src.engine import ExecutionEngine, ExecutionResult
from src.evaluator import Evaluator, EvaluationScore
from src.memory import StateStore, AttemptRecord
from src.profiler import format_hotspots
from src.data_loader import load_real_test_cases
from src.diff_engine import generate_diff


class IterationController:
    def __init__(self, parser: ProblemParser, generator: HypothesisGenerator, engine: ExecutionEngine, evaluator: Evaluator, store: StateStore):
        self.parser = parser
        self.generator = generator
        self.engine = engine
        self.evaluator = evaluator
        self.store = store
        self.baseline_result = None
        self.latest_hotspots = []

    def run_baseline(self, problem: ParsedProblem, baseline_code: str, constraints: dict = None) -> Dict[str, Any]:
        """Benchmark the user's baseline code and profile it."""
        print("🚩 Running baseline benchmark + profiling...")
        test_cases = [tc.dict() for tc in problem.test_cases]
        result = self.engine.run_experiment(baseline_code, test_cases)
        eval_score = self.evaluator.evaluate(result.dict(), result.runtime, result.memory, constraints)

        self.latest_hotspots = result.hotspots
        if self.latest_hotspots:
            print(f"  🔬 Profiled baseline. Top hotspot: Line {self.latest_hotspots[0]['line']} ({self.latest_hotspots[0]['time_us']}μs)")

        self.baseline_result = {
            "approach": "Baseline (User Code)",
            "code": baseline_code,
            "compute_cost": eval_score.compute_cost,
            "is_valid": eval_score.is_valid,
            "runtime": result.runtime,
            "memory": result.memory,
            "hotspots": self.latest_hotspots,
            "explanation": "Original user code."
        }

        self.store.save_attempt(
            iteration=-1,
            approach="Baseline",
            code=baseline_code,
            score=eval_score.compute_cost,
            passed=eval_score.is_valid,
            runtime=result.runtime,
            output=result.stdout
        )
        return self.baseline_result

    def solve(self, user_input: str, baseline_code: str = None, max_iterations: int = 3,
              constraints: dict = None, real_test_cases_path: str = None, guardrails: List[str] = None) -> Dict[str, Any]:
        """
        The core loop: parse → profile → hypothesize (targeted) → execute → evaluate → iterate.
        """
        # 1. Parse
        parsed_problem = self.parser.parse(user_input)

        # 2. Override with real test cases if provided
        if real_test_cases_path:
            real_tcs = load_real_test_cases(real_test_cases_path)
            if real_tcs:
                from src.parser import TestCase
                parsed_problem.test_cases = [TestCase(**tc) for tc in real_tcs]
                print(f"  📂 Loaded {len(real_tcs)} real test cases from {real_test_cases_path}")

        # 3. Baseline
        if baseline_code:
            self.run_baseline(parsed_problem, baseline_code, constraints)

        iteration_progress = []

        for i in range(max_iterations):
            print(f"\n🔄 Iteration {i+1}/{max_iterations}...")

            # 4. Generate hypotheses (targeted if we have hotspots)
            if i == 0:
                hypotheses = self.generator.generate(
                    parsed_problem.dict(), count=5,
                    hotspots=self.latest_hotspots if self.latest_hotspots else None,
                    guardrails=guardrails
                )
            else:
                top_attempts = self.store.get_top_attempts(limit=2)
                hypotheses = self._refine_solutions(parsed_problem, top_attempts, guardrails)

            iter_best_score = -1.0
            iter_best_hotspots = []

            # 5. Execute & Evaluate
            for h in hypotheses:
                test_cases = [tc.dict() for tc in parsed_problem.test_cases]
                result = self.engine.run_experiment(h.code, test_cases)
                eval_score = self.evaluator.evaluate(result.dict(), result.runtime, constraints)

                self.store.save_attempt(
                    iteration=i,
                    approach=h.approach,
                    code=h.code,
                    score=eval_score.score,
                    passed=result.passed,
                    runtime=result.runtime,
                    output=result.stdout
                )

                if eval_score.is_valid and eval_score.compute_cost < iter_best_cost:
                    iter_best_cost = eval_score.compute_cost
                    iter_best_hotspots = result.hotspots

            # Update hotspots for next iteration's targeted generation
            if iter_best_hotspots:
                self.latest_hotspots = iter_best_hotspots

            iteration_progress.append({
                "iteration": i + 1,
                "best_cost": iter_best_cost
            })
            print(f"  ✨ Iteration {i+1} done. Best compute cost: {iter_best_cost:.6f} GB-s")

        # Final synthesis
        # We want the lowest score, so order by ASC (score is compute_cost here)
        all_attempts = self.store.get_top_attempts(limit=10)
        # Filter only passed
        valid_attempts = [a for a in all_attempts if a.passed]
        # Sort by score ascending (lowest compute cost)
        valid_attempts.sort(key=lambda x: x.score)
        
        top_3 = valid_attempts[:3]
        best_overall = top_3[0] if top_3 else None

        # Check if we actually improved over baseline
        baseline_cost = self.baseline_result["compute_cost"] if self.baseline_result else float('inf')
        
        improvement_explanation = ""
        tradeoffs = ""
        no_improvement = False
        
        if self.baseline_result and best_overall:
            if best_overall.score < baseline_cost * 0.99:  # At least 1% improvement to matter
                explanation_data = self.explain_improvement(self.baseline_result, best_overall.dict())
                improvement_explanation = explanation_data.get("improvements", "")
                tradeoffs = explanation_data.get("tradeoffs", "")
            else:
                no_improvement = True
                best_overall = None  # Rollback structurally to baseline
                print("\\n⚠️ OPTIMIZATION REJECTED: Baseline already optimal under current constraints.")

        # Generate diff
        diff_output = ""
        if self.baseline_result and best_overall and not no_improvement:
            diff_output = generate_diff(self.baseline_result["code"], best_overall.code)

        return {
            "baseline": self.baseline_result,
            "top_solutions": [t.dict() for t in top_3],
            "best_solution": best_overall.dict() if best_overall else None,
            "no_improvement": no_improvement,
            "iteration_progress": iteration_progress,
            "improvement_explanation": improvement_explanation,
            "tradeoffs": tradeoffs,
            "diff": diff_output,
            "parsed_problem": parsed_problem.dict(),
            "constraints": constraints,
            "summary": f"Completed {max_iterations} iterations."
        }

    def explain_improvement(self, baseline: dict, optimized: dict) -> dict:
        """LLM-powered explanation of improvements and tradeoffs."""
        hotspot_context = ""
        if baseline.get("hotspots"):
            hotspot_context = f"\\nBaseline hotspots:\\n{format_hotspots(baseline['hotspots'])}"

        prompt = f"""
Compare the Baseline Code to the Optimized Code.
Extract the technical improvements and the tradeoffs (what we gave up for speed).

Baseline Code:
{baseline['code']}
Cost: {baseline['compute_cost']:.6f} GB-s
{hotspot_context}

Optimized Code:
{optimized['code']}
Cost: {optimized['score']:.6f} GB-s

Output JSON format strictly:
{{
   "improvements": "- Reason 1\\n- Reason 2",
   "tradeoffs": "- Tradeoff 1 (e.g. less flexible, assumes fixed schema)\\n- Tradeoff 2"
}}
"""
        response = completion(
            model=self.generator.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def _refine_solutions(self, problem: ParsedProblem, top_attempts: List[Any], guardrails: List[str] = None) -> List[Hypothesis]:
        """Targeted refinement using profiling data."""
        context = []
        for a in top_attempts:
            context.append({
                "approach": a.approach,
                "code": a.code,
                "score": a.score,
                "passed": a.passed,
                "runtime": a.runtime
            })

        hotspot_section = ""
        if self.latest_hotspots:
            hotspot_section = f"""
PROFILING DATA — Current hotspots:
{format_hotspots(self.latest_hotspots)}

Target these specific lines to minimize compute cost (GB-seconds).
"""

        gr_section = ""
        if guardrails:
            gr_section = "\\nSTRICT GUARDRAILS (Must not violate):\\n" + "\\n".join([f"- {g}" for g in guardrails]) + "\\n"

        prompt = f"""
Given the problem and previous attempts, generate 3 radically optimized solutions.

Problem:
{problem.json()}

Top previous results:
{json.dumps(context, indent=2)}
{hotspot_section}
{gr_section}

Output format:
{{
    "hypotheses": [
        {{
            "approach": "Refinement of ...",
            "code": "python code...",
            "explanation": "..."
        }},
        ...
    ]
}}
"""
        response = completion(
            model=self.generator.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        data = json.loads(response.choices[0].message.content)
        return [Hypothesis(**h) for h in data.get("hypotheses", [])]
