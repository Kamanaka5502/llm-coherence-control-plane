# actuation_threshold.py
# Thresholded actuation gate
# Determines whether action is permitted (no execution)

from typing import Dict


DEFAULT_CONFIDENCE_THRESHOLD = 0.75


def may_act(
    confidence: float,
    invariant_status: Dict,
    policy_snapshot: Dict | None = None,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> Dict[str, str]:
    """
    Determine whether actuation is permitted.
    Returns a decision record only.
    """

    # Invariants are absolute
    if invariant_status.get("status") != "CLEAN":
        return {
            "decision": "DENY",
            "reason": "invariants not clean"
        }

    # Confidence gate
    if confidence < threshold:
        return {
            "decision": "DENY",
            "reason": "confidence below threshold"
        }

    # Policy gate (if present)
    if policy_snapshot:
        if not policy_snapshot.get("allow_action", True):
            return {
                "decision": "DENY",
                "reason": "policy prohibits action"
            }

    return {
        "decision": "ALLOW",
        "reason": "all thresholds satisfied"
    }
