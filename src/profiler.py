"""
Line-level profiler: finds exactly WHERE time is wasted in candidate code.
Returns the top N hotspots sorted by cumulative time.
"""
import importlib.util
import tempfile
import os
from line_profiler import LineProfiler
from typing import List, Dict, Any, Optional


def load_function_from_code(code: str, func_name: str = "solve"):
    """Dynamically load a function from a code string."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    spec = importlib.util.spec_from_file_location("dynamic_module", tmp_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func = getattr(module, func_name, None)
    if func is None:
        os.remove(tmp_path)
        raise ValueError(f"Function '{func_name}' not found in provided code.")

    return func, tmp_path


def profile_code(code: str, test_input: Any, func_name: str = "solve", top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Profile the given code's function with line-level granularity.
    Returns the top N hotspot lines sorted by cumulative time.
    """
    func, path = load_function_from_code(code, func_name)

    profiler = LineProfiler()
    profiler.add_function(func)

    profiler.enable()
    try:
        func(test_input)
    finally:
        profiler.disable()

    results = []
    stats = profiler.get_stats()
    for (filename, lineno, funcname), timings in stats.timings.items():
        for line_no, hits, time_us in timings:
            results.append({
                "line": line_no,
                "hits": hits,
                "time_us": time_us,  # microseconds
                "function": funcname
            })

    os.remove(path)

    # Sort by time spent (descending)
    results.sort(key=lambda x: x["time_us"], reverse=True)
    return results[:top_n]


def format_hotspots(hotspots: List[Dict[str, Any]]) -> str:
    """Format hotspot data into a human-readable string for LLM prompts."""
    if not hotspots:
        return "No hotspots detected."
    
    lines = []
    for h in hotspots:
        lines.append(f"  Line {h['line']}: {h['time_us']}μs ({h['hits']} hits)")
    return "\n".join(lines)
