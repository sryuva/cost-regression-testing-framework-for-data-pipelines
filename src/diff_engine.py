"""
Diff Engine: generates unified diffs between original and optimized code.
Provides a trust layer so users can see exactly what changed.
"""
import difflib
from typing import Optional


def generate_diff(original: str, optimized: str, context_lines: int = 3) -> str:
    """
    Generate a unified diff between original and optimized code.
    Returns a string showing additions (+), deletions (-), and context.
    """
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        optimized.splitlines(keepends=True),
        fromfile="baseline.py",
        tofile="optimized.py",
        n=context_lines
    )
    return "".join(diff)


def generate_side_by_side(original: str, optimized: str) -> str:
    """
    Generate a side-by-side comparison summary.
    Useful for quick visual inspection.
    """
    orig_lines = original.splitlines()
    opt_lines = optimized.splitlines()
    
    differ = difflib.SequenceMatcher(None, orig_lines, opt_lines)
    
    changes = []
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == "replace":
            changes.append(f"CHANGED lines {i1+1}-{i2}:")
            for line in orig_lines[i1:i2]:
                changes.append(f"  - {line}")
            for line in opt_lines[j1:j2]:
                changes.append(f"  + {line}")
        elif tag == "delete":
            changes.append(f"REMOVED lines {i1+1}-{i2}:")
            for line in orig_lines[i1:i2]:
                changes.append(f"  - {line}")
        elif tag == "insert":
            changes.append(f"ADDED after line {i1}:")
            for line in opt_lines[j1:j2]:
                changes.append(f"  + {line}")
    
    if not changes:
        return "No differences found."
    
    return "\n".join(changes)
