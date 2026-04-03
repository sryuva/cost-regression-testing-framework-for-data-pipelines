try:
    from .compare import compare_runs
    from .runner import run_n
except ImportError:
    from compare import compare_runs
    from runner import run_n

MIN_RUNTIME = 0.1


def should_flag(delta, confidence, ignored):
    if ignored:
        return False
    if delta > 1.0:
        return True
    return delta > 0.2 and confidence > 0.8


def format_output(
    delta,
    confidence,
    fn_deltas,
    flagged=False,
    ignored=False,
    reason="",
    limited_attribution=False,
):
    if ignored:
        return f"Performance Check\n\nNo significant regression detected\nIgnored: {reason}"

    pct = round(delta * 100, 1)

    lines = []
    if flagged:
        lines.append("Performance Check: BLOCK")
    else:
        lines.append("Performance Check")
    lines.append("")
    lines.append(f"{'+' if pct >= 0 else ''}{pct}% runtime change")
    lines.append(f"Confidence: {confidence:.2f}")
    if not flagged:
        lines.append("")
        lines.append("No significant regression detected")

    if fn_deltas:
        lines.append("\nTop contributors:")
        for fn, change in fn_deltas:
            sign = "+" if change >= 0 else ""
            lines.append(f"- {fn}: {sign}{round(change * 100, 1)}%")
        top_fn = fn_deltas[0][0]
        lines.append("")
        lines.append(f"Suggestion: Inspect {top_fn}() for recent changes")
    elif limited_attribution:
        lines.append("")
        lines.append("Limited attribution")
        lines.append("No tracked functions found.")
        lines.append("Add @track_time to key steps for better insights.")

    return "\n".join(lines)


def run_check(pr_func, base_func, input_data):
    base = run_n(base_func, input_data, n=3)
    pr = run_n(pr_func, input_data, n=3)

    ignored = base["median_runtime"] < MIN_RUNTIME and pr["median_runtime"] < MIN_RUNTIME
    ignore_reason = "runtime too small to evaluate" if ignored else ""

    delta, confidence, fn_deltas = compare_runs(base, pr)
    observed = set(base.get("fn_times", {}).keys()) | set(pr.get("fn_times", {}).keys())
    outer_only = {base_func.__name__, pr_func.__name__}
    limited_attribution = all(fn in outer_only for fn in observed) or not observed
    if limited_attribution:
        fn_deltas = []
    flag = should_flag(delta, confidence, ignored)

    result = format_output(
        delta,
        confidence,
        fn_deltas,
        flagged=flag,
        ignored=ignored,
        reason=ignore_reason,
        limited_attribution=limited_attribution,
    )

    return {
        "flag": flag,
        "ignore": ignored,
        "reason": ignore_reason,
        "limited_attribution": limited_attribution,
        "summary": result,
        "delta": delta,
        "confidence": confidence,
    }
