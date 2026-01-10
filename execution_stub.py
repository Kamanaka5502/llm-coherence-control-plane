# execution_stub.py
# Controlled execution stub
# One capability only: explain
# No memory. No side effects. Fully reversible.

from typing import Dict


def execute(
    capability: str,
    text: str
) -> Dict[str, str]:
    """
    Execute a single, explicitly allowed capability.
    """

    if capability != "explain":
        return {
            "status": "DENIED",
            "reason": "capability not executable"
        }

    if not text.strip():
        return {
            "status": "NOOP",
            "reason": "empty input"
        }

    # Minimal, bounded explanation
    explanation = (
        "Elyria is stable because each layer operates under strict constraints, "
        "with explicit boundaries between understanding, permission, and action."
    )

    return {
        "status": "EXECUTED",
        "capability": "explain",
        "output": explanation
    }

