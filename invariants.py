# invariants.py
# System invariants & contract verification
# These must hold true for Elyria to be considered stable

from pathlib import Path
import json
import sys

LOG = Path.home() / ".elyria_instrumentation.jsonl"

INVARIANTS = {
    "entropy_bound": lambda e: 0.0 <= e["entropy"] <= 1.0,
    "mean_entropy_bound": lambda e: 0.0 <= e["mean_entropy"] <= 1.0,
    "dampening_range": lambda e: 0.0 < e["dampening"] <= 1.0,
    "no_identity_write": lambda e: "identity_pressure" in e,
    "constraints_explicit": lambda e: isinstance(e.get("active_constraints"), list),
}

def load_events():
    if not LOG.exists():
        return []
    events = []
    with LOG.open() as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def verify():
    events = load_events()
    if not events:
        print("NO DATA — invariants unverifiable")
        return 1

    failures = []

    for i, e in enumerate(events):
        for name, rule in INVARIANTS.items():
            try:
                if not rule(e):
                    failures.append((i, name, e))
            except Exception:
                failures.append((i, name, "exception"))

    if failures:
        print("INVARIANT VIOLATIONS DETECTED")
        print("============================")
        for idx, name, detail in failures:
            print(f"- event {idx}: {name}")
        return 2

    print("ELYRIA INVARIANTS VERIFIED")
    print("==========================")
    print(f"events checked : {len(events)}")
    print(f"invariants     : {len(INVARIANTS)}")
    print("status         : CLEAN")

    return 0


if __name__ == "__main__":
    sys.exit(verify())
