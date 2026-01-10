# observability.py
# Human-facing, read-only view of recent system behavior

from pathlib import Path
import json

LOG = Path.home() / ".elyria_instrumentation.jsonl"
WINDOW = 20


def load_recent(n=WINDOW):
    if not LOG.exists():
        return []

    lines = LOG.read_text().splitlines()
    recent = lines[-n:]
    events = []

    for line in recent:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    return events


def trend(values):
    if len(values) < 2:
        return "→"
    if values[-1] > values[0]:
        return "↑"
    if values[-1] < values[0]:
        return "↓"
    return "→"


def summarize():
    events = load_recent()
    if not events:
        print("no recent data")
        return

    entropies = [e["entropy"] for e in events]
    mean_entropies = [e["mean_entropy"] for e in events]
    dampenings = [e["dampening"] for e in events]

    stabilized = sum(
        1 for e in events if "stabilize" in e.get("active_constraints", [])
    )

    print(f"ELYRIA OBSERVABILITY (last {len(events)} events)")
    print("--------------------------------------")
    print(f"entropy trend        : {trend(entropies)}")
    print(f"mean entropy trend   : {trend(mean_entropies)}")
    print(f"dampening trend      : {trend(dampenings)}")
    print(f"stabilizations       : {stabilized}")
    print(f"avg entropy          : {sum(entropies)/len(entropies):.4f}")
    print(f"avg dampening        : {sum(dampenings)/len(dampenings):.3f}")


if __name__ == "__main__":
    summarize()
