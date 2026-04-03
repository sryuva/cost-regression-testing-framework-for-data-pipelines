import time
from collections import defaultdict
from functools import wraps

FUNCTION_TIMES = defaultdict(float)


def track_time(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        duration = time.perf_counter() - start
        FUNCTION_TIMES[fn.__name__] += duration
        return result

    return wrapper


def reset():
    FUNCTION_TIMES.clear()


def get_times():
    return dict(FUNCTION_TIMES)
