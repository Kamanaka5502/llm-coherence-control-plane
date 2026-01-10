# confidence.py
# Confidence estimation layer
# Reports certainty without altering reasoning

from typing import Dict


def compute_confidence(
    gate_snapshot: Dict | None = None,
    invariant_status: Dict | None = None
) -> float:
    """
    Compute a bounded confidence score in [0.0, 1.0]
    based only on measurable system pressure.
    """
    # Defaults: neutral, safe
    entropy = 0.0
    stabilized = False
    invariant_clean = True

    if gate_snapshot:
        entropy = gate_snapshot.get("mean_entropy", 0.0)
        stabilized = "stabilize" in gate_snapshot.get("active_constraints", [])

    if invariant_status:
        invariant_clean = invariant_status.get("status", "CLEAN") == "CLEAN"

    # Start from full confidence
    confidence = 1.0

    # Entropy penalty (soft)
    confidence -= min(entropy, 1.0) * 0.4

    # Stabilization penalty
    if stabilized:
        confidence -= 0.2

    # Invariant violation is hard stop
    if not invariant_clean:
        confidence = 0.0

    return round(max(0.0, min(confidence, 1.0)), 3)
