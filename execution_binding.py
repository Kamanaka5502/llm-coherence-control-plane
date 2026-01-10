# execution_binding.py
# Final execution gate
# Explicit opt-in only

from typing import Dict, List


def may_execute(
    capabilities: List[str],
    mode: str = "dry-run",
    operator_ok: bool = False
) -> Dict[str, str]:
    """
    Decide whether execution is permitted.
    Default: deny.
    """

    if mode != "execute":
        return {
            "decision": "DENY",
            "reason": "execution mode not enabled"
        }

    if not operator_ok:
        return {
            "decision": "DENY",
            "reason": "operator approval not present"
        }

    if not capabilities:
        return {
            "decision": "DENY",
            "reason": "no executable capabilities"
        }

    return {
        "decision": "ALLOW",
        "reason": "explicit execution binding satisfied"
    }
