# policy.py
# Advisory policy layer (read-only)
# Consumes metrics + observability signals
# Emits recommendations, never actions

from pathlib import Path
import json

METRICS_LOG = Path.home() / ".elyria_instrumentation.jsonl"

# Tunable advisory thresholds (NOT enforced)
ENTROPY_TARGET = 0.35
STABILIZATION_TARGET = 0.60
DAMPENING_TARGET = 0.80


def load_events():
    if not METRICS_LOG.exists():
        return []

    events = []
    with METRICS_LOG.open() as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def analyze():
    events = load_events()
    if not events:
        return {
            "status": "no-data",
            "recommendations": ["collect more observations"]
        }

    total = len(events)

    avg_entropy = sum(e["entropy"] for e in events) / total
    avg_dampening = sum(e["dampening"] for e in events) / total
    stabilization_rate = sum(
        1 for e in events if "stabilize" in e.get("active_constraints", [])
    ) / total

    recs = []

    if avg_entropy > ENTROPY_TARGET:
        recs.append("consider lowering ENTROPY_MAX")

    if stabilization_rate > STABILIZATION_TARGET:
        recs.append("system frequently stabilizing; review input patterns")

    if avg_dampening < DAMPENING_TARGET:
        recs.append("dampening low; entropy may be over-constrained")

    if not recs:
        recs.append("system operating within expected bounds")

    return {
        "observations": total,
        "avg_entropy": round(avg_entropy, 4),
        "stabilization_rate": round(stabilization_rate, 3),
        "avg_dampening": round(avg_dampening, 3),
        "recommendations": recs,
    }


def main():
    report = analyze()

    print("ELYRIA POLICY ADVISORY")
    print("======================")
    for k, v in report.items():
        print(f"{k:22}: {v}")


if __name__ == "__main__":
    main()

