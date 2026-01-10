# dispatch.py
# Capability dispatch (dry-run only)
# No execution. No side effects.

from typing import Dict, List


def dispatch(capabilities: List[str], text: str) -> Dict[str, str]:
    """
    Describe what would happen if capabilities were executed.
    """

    if not capabilities:
        return {
            "status": "noop",
            "description": "No capabilities permitted for this intent."
        }

    descriptions = []

    for cap in capabilities:
        if cap == "explain":
            descriptions.append(
                "System would generate an explanation based solely on explicit input."
            )
        else:
            descriptions.append(
                f"Capability '{cap}' has no defined dispatch behavior."
            )

    return {
        "status": "dry-run",
        "description": " ".join(descriptions)
    }
