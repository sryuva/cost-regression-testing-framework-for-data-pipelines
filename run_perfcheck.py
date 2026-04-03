from perfcheck.main import run_check
from perfcheck.profiler import track_time
from task import transform as pr_transform


@track_time
def baseline_transform(data):
    return [x * 2 for x in data]


@track_time
def pr_callable(data):
    return pr_transform(data)


def main():
    input_data = list(range(2000000))
    result = run_check(pr_callable, baseline_transform, input_data)

    text = result["summary"]
    if result["flag"]:
        text = "Performance Check: BLOCK\n\n" + text
    elif result.get("ignore"):
        text = "Performance Check: IGNORE\n\n" + text
    else:
        text = "Performance Check: OK\n\n" + text

    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")

    print(text)


if __name__ == "__main__":
    main()
