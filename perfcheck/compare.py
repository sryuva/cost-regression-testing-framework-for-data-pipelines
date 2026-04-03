try:
    from .stats import compute_confidence
except ImportError:
    from stats import compute_confidence


def compare_functions(base_times, pr_times, min_change=0.1):
    results = []

    for fn in pr_times:
        if fn in base_times and base_times[fn] > 0:
            change = (pr_times[fn] - base_times[fn]) / base_times[fn]
            if change > min_change:
                results.append((fn, change))
        elif fn not in base_times and pr_times[fn] > 0:
            # PR-only timed function: treat as new overhead to surface attribution.
            results.append((fn, 1.0))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:3]


def compare_runs(base, pr):
    delta = (pr["median_runtime"] - base["median_runtime"]) / base["median_runtime"]

    confidence = min(
        compute_confidence(base["std_runtime"], base["median_runtime"]),
        compute_confidence(pr["std_runtime"], pr["median_runtime"]),
    )

    fn_deltas = compare_functions(base["fn_times"], pr["fn_times"])

    return delta, confidence, fn_deltas
