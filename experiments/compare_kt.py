import json
from pathlib import Path

def load_kt(path):
    kt = []
    with open(path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if "Kt" in record:
                kt.append(record["Kt"])
            elif "kt" in record:
                kt.append(record["kt"])
            elif "Kₜ" in record:
                kt.append(record["Kₜ"])
    return kt


def summarize(label, values):
    if not values:
        print(f"{label}: no Kt data found")
        return
    print(f"{label}")
    print(f"  steps: {len(values)}")
    print(f"  start: {values[0]:.2f}")
    print(f"  end:   {values[-1]:.2f}")
    print(f"  delta: {values[-1] - values[0]:.2f}")
    print()


if __name__ == "__main__":
    before = Path("experiments/data/before.jsonl")
    after = Path("experiments/data/after.jsonl")

    kt_before = load_kt(before)
    kt_after = load_kt(after)

    summarize("BEFORE (unchecked recursion)", kt_before)
    summarize("AFTER (ECP enforced)", kt_after)
