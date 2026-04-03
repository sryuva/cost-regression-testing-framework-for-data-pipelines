from perfcheck.main import run_check
from task import run_task as baseline
from task import run_task as pr_version


def main():
    # input/output paths are part of callable signature; task ignores input content in this testpack.
    result = run_check(pr_version, baseline, ("in.txt", "out.txt"))

    # Support callables expecting single input arg by adapting below wrappers.
    # Here, task signature is two-arg, so we wrap them.

if __name__ == "__main__":
    def base_wrapper(_):
        return baseline("input.txt", "baseline_out.txt")

    def pr_wrapper(_):
        return pr_version("input.txt", "pr_out.txt")

    result = run_check(pr_wrapper, base_wrapper, 0)

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
