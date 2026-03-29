"""
Execution Engine: runs code in isolated subprocess + optional line-level profiling.
"""
import subprocess
import time
import os
import tempfile
import json
from pydantic import BaseModel
from typing import List, Any, Dict, Optional

from src.profiler import profile_code, format_hotspots


class ExecutionResult(BaseModel):
    passed: bool
    runtime: float
    memory: float
    error: str = ""
    stdout: str = ""
    hotspots: List[Dict[str, Any]] = []


class ExecutionEngine:
    def __init__(self, timeout: float = 10.0, enable_profiling: bool = True):
        self.timeout = timeout
        self.enable_profiling = enable_profiling

    def _run_single_experiment(self, code: str, test_cases: List[Dict[str, Any]]) -> ExecutionResult:
        """Run code against test cases in a subprocess. Optionally profile."""
        harness = f"""
import json
import time
import sys
import tracemalloc

{code}

test_cases = {test_cases}
results = []
passed_all = True

tracemalloc.start()

for i, tc in enumerate(test_cases):
    try:
        if 'solve' not in globals():
            raise ValueError("No 'solve' function found in generated code.")
            
        start = time.perf_counter()
        result = solve(tc['input'])
        end = time.perf_counter()
        
        expected = tc['expected_output']
        # Convert result to JSON and back to match types (e.g. tuples to lists)
        try:
            result_normalized = json.loads(json.dumps(result))
        except (TypeError, ValueError):
            result_normalized = str(result)
            
        if result_normalized == expected:
            results.append({{"index": i, "passed": True, "time": end - start}})
        else:
            results.append({{"index": i, "passed": False, "actual": str(result), "expected": str(expected)}})
            passed_all = False
    except Exception as e:
        results.append({{"index": i, "passed": False, "error": str(e)}})
        passed_all = False

_, peak_memory_bytes = tracemalloc.get_traced_memory()
tracemalloc.stop()
peak_memory_mb = peak_memory_bytes / (1024 * 1024)

final_output = {{"passed": passed_all, "results": results, "peak_memory_mb": peak_memory_mb}}
print("---END_OF_RESULTS---")
print(json.dumps(final_output))
"""

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write(harness)
            temp_path = f.name

        start_time = time.perf_counter()
        try:
            res = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            total_runtime = time.perf_counter() - start_time

            if res.returncode != 0:
                return ExecutionResult(passed=False, runtime=total_runtime, memory=0.0, error=res.stderr, stdout=res.stdout)

            parts = res.stdout.split("---END_OF_RESULTS---")
            if len(parts) < 2:
                return ExecutionResult(passed=False, runtime=total_runtime, memory=0.0, error="Protocol error: No result marker found", stdout=res.stdout)

            parsed_res = json.loads(parts[1].strip())
            passed = parsed_res.get("passed", False)
            peak_memory = parsed_res.get("peak_memory_mb", 0.0)

            # Line-level profiling (only on passing code, using first test case)
            hotspots = []
            if self.enable_profiling and passed and test_cases:
                try:
                    hotspots = profile_code(code, test_cases[0]["input"])
                except Exception:
                    pass  # Profiling is best-effort, never block the pipeline

            return ExecutionResult(
                passed=passed,
                runtime=total_runtime,
                memory=peak_memory,
                stdout=res.stdout,
                hotspots=hotspots
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(passed=False, runtime=self.timeout, memory=0.0, error="Execution timed out")
        except Exception as e:
            return ExecutionResult(passed=False, runtime=0.0, memory=0.0, error=f"Internal engine error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def run_experiment(self, code: str, test_cases: List[Dict[str, Any]]) -> ExecutionResult:
        """Run code against test cases 3 times and average results for stability."""
        runtimes = []
        memories = []
        last_res = None
        
        for _ in range(3):
            res = self._run_single_experiment(code, test_cases)
            if not res.passed:
                return res  # Fast fail
            runtimes.append(res.runtime)
            memories.append(res.memory)
            last_res = res
            
        avg_runtime = sum(runtimes) / 3.0
        avg_memory = sum(memories) / 3.0
        
        return ExecutionResult(
            passed=True,
            runtime=avg_runtime,
            memory=avg_memory,
            error=last_res.error,
            stdout=last_res.stdout,
            hotspots=last_res.hotspots
        )
