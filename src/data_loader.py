"""
Real input loader: replaces fake/generated test cases with actual production-like data.
Supports JSON files and inline lists.
"""
import json
import os
from typing import List, Any, Optional


def load_real_inputs(path: str = "data/inputs.json") -> List[Any]:
    """Load real test inputs from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}. Create it with real production data.")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Input file must contain a JSON array of test inputs.")
    
    return data


def load_real_test_cases(path: str = "data/test_cases.json") -> List[dict]:
    """
    Load real test cases (input + expected_output pairs) from a JSON file.
    Format: [{"input": ..., "expected_output": ...}, ...]
    """
    if not os.path.exists(path):
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Test cases file must contain a JSON array.")
    
    return data
