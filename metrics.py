# metrics.py
# Aggregation layer (read-only)
# Summarizes instrumentation without influence

from pathlib import Path
import json

LOG = Path.home() / ".elyria_instrumentation.jsonl"


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


def summarize():
    events = load_events()
    if not events:
        print("no instrumentation data")
        return

    total = len(events)

    avg_entropy = sum(e["entropy"] for e in events) / total
    avg_mean_entropy = sum(e["mean_entropy"] for e in events) / total
    avg_dampening = sum(e["dampening"] for e in events) / total

    stabilized = sum(
        1 for e in events if "stabilize" in e.get("active_constraints", [])
    )

    print("ELYRIA METRICS")
    print("-------------------------")
    print(f"observations        : {total}")
    print(f"avg entropy         : {avg_entropy:.4f}")
    print(f"avg mean entropy    : {avg_mean_entropy:.4f}")
    print(f"stabilization rate  : {stabilized / total:.2%}")
    print(f"avg dampening       : {avg_dampening:.3f}")

if __name__ == "__main__":
    summarize()
