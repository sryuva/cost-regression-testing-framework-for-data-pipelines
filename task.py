from perfcheck.profiler import track_time


@track_time
def transform(data):
    out = []
    for x in data:
        s = 0
        for _ in range(3):
            s += x
        out.append(s)
    return out


def run_task(input_path: str, output_path: str):
    nums = list(range(300000))
    out = transform(nums)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(len(out)))
