# reflection.py
# Read-only reflection layer
# No memory. No authority. No actuation.

from typing import Dict


def reflect(
    text: str,
    reasoning: Dict,
    orchestration: Dict,
    confidence: float
) -> Dict[str, str]:
    """
    Produce a bounded reflection over the current interaction.
    Reflection is descriptive only.
    """

    if not text.strip():
        return {
            "status": "no-input",
            "reflection": ""
        }

    reflection = (
        "The system processed an explicit input under bounded reasoning. "
        f"Input type was '{orchestration.get('type')}' with intent "
        f"'{orchestration.get('intent')}'. "
        f"Confidence level was {confidence:.2f}. "
        "No memory was accessed and no action was taken."
    )

    return {
        "status": "ok",
        "reflection": reflection
    }
