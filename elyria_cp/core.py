from datetime import datetime, UTC

def inflate(text: str, history: list[dict]) -> dict:
    """
    Intelligence Inflation Core
    - evaluates new input against prior state
    - returns an enriched node
    """

    strength = 1.0

    if history:
        last = history[-1]["text"]
        if last.strip().lower() == text.strip().lower():
            strength = 0.5  # repetition dampening
        else:
            strength = min(1.0, 0.7 + (len(text) / 200))

    return {
        "text": text,
        "ts": datetime.now(UTC).isoformat(),
        "strength": round(strength, 3),
    }

