from perfcheck.profiler import track_time


@track_time
def transform(data):
    return [x * 2 for x in data]


def run_task(input_path: str, output_path: str):
    nums = list(range(300000))
    out = transform(nums)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(len(out)))
