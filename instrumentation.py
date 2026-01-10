# instrumentation.py
# Read-only observability layer
# Records intelligence gate behavior without influence

from pathlib import Path
from datetime import datetime, timezone
import json

LOG = Path.home() / ".elyria_instrumentation.jsonl"


def record(snapshot: dict, dampening: float):
    """
    Append a single observation record.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "entropy": snapshot.get("entropy"),
        "mean_entropy": snapshot.get("mean_entropy"),
        "active_constraints": snapshot.get("active_constraints", []),
        "identity_pressure": snapshot.get("identity_pressure"),
        "dampening": dampening,
    }

    with LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
