# intent_bindings.py
# Explicit intent → capability binding
# No execution. No side effects.

from typing import Dict, List


# Static binding table
INTENT_BINDINGS: Dict[str, List[str]] = {
    "statement": [],
    "explanation": ["explain"],
    "question": ["explain"],
    "request": [],
}


def allowed_capabilities(
    intent: str,
    confidence: float,
    invariant_status: Dict
) -> Dict[str, object]:
    """
    Determine which capabilities are allowed for a given intent.
    """

    if invariant_status.get("status") != "CLEAN":
        return {
            "allowed": [],
            "reason": "invariants not clean"
        }

    if confidence < 0.5:
        return {
            "allowed": [],
            "reason": "confidence too low"
        }

    allowed = INTENT_BINDINGS.get(intent, [])

    return {
        "allowed": allowed,
        "reason": "explicit binding"
    }
