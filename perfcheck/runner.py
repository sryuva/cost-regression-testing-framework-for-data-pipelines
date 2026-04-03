import statistics
import time

import psutil

try:
    from .profiler import get_times, reset, track_time
except ImportError:
    from profiler import get_times, reset, track_time


def run_once(func, input_data):
    reset()
    timed_func = track_time(func)

    process = psutil.Process()
    start = time.perf_counter()

    timed_func(input_data)

    runtime = time.perf_counter() - start
    memory = process.memory_info().rss
    fn_times = get_times()

    return runtime, memory, fn_times


def aggregate_fn_times(runs):
    agg = {}
    for run in runs:
        for fn, t in run.items():
            agg.setdefault(fn, []).append(t)

    return {fn: statistics.median(times) for fn, times in agg.items()}


def run_n(func, input_data, n=3):
    runtimes = []
    memories = []
    fn_time_runs = []

    for _ in range(n):
        r, m, ft = run_once(func, input_data)
        runtimes.append(r)
        memories.append(m)
        fn_time_runs.append(ft)

    return {
        "median_runtime": statistics.median(runtimes),
        "std_runtime": statistics.stdev(runtimes) if n > 1 else 0,
        "median_memory": statistics.median(memories),
        "fn_times": aggregate_fn_times(fn_time_runs),
    }
