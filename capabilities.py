# capabilities.py
# Stateless capability functions
# No memory, no authority, no side effects

from typing import Dict, List


def classify(text: str) -> Dict[str, str]:
    """
    Simple structural classification of input.
    """
    text = text.strip()
    if not text:
        return {"type": "empty"}

    if text.endswith("?"):
        return {"type": "question"}

    if text.lower().startswith(("please", "do ", "can you")):
        return {"type": "request"}

    return {"type": "statement"}


def extract_intent(text: str) -> Dict[str, str]:
    """
    Extract high-level intent without inference.
    """
    text = text.lower()

    if "why" in text:
        return {"intent": "explanation"}

    if "how" in text:
        return {"intent": "procedure"}

    if "should" in text or "can i" in text:
        return {"intent": "decision_support"}

    return {"intent": "unspecified"}


def summarize(text: str, max_words: int = 12) -> Dict[str, str]:
    """
    Naive summarization (deterministic, bounded).
    """
    words = text.split()
    return {
        "summary": " ".join(words[:max_words])
    }
