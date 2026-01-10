# orchestrator.py
# Thin orchestration layer: routes explicit input to stateless capabilities
# No memory, no authority, no side effects.

from typing import Dict, Optional
from capabilities import classify, extract_intent, summarize


def route(text: str, context: Optional[Dict] = None) -> Dict:
    """
    Route input to selected capabilities based on explicit text + optional context.
    Returns structured results only.
    """
    if context is None:
        context = {}

    text = (text or "").strip()
    if not text:
        return {
            "status": "no-input",
            "used": [],
            "results": {}
        }

    # Always-safe baseline signals
    c = classify(text)
    i = extract_intent(text)

    used = ["classify", "extract_intent"]
    results = {
        "classify": c,
        "extract_intent": i
    }

    # Optional summarization (explicitly allowed via context)
    allow_summary = bool(context.get("allow_summary", True))
    if allow_summary:
        s = summarize(text, max_words=int(context.get("summary_words", 12)))
        used.append("summarize")
        results["summarize"] = s

    return {
        "status": "ok",
        "used": used,
        "results": results
    }


def main():
    print("ELYRIA ORCHESTRATOR (THIN)")
    print("--------------------------")
    text = input("route → ").strip()

    # Explicit, opt-in context (does not imply authority)
    context = {
        "allow_summary": True,
        "summary_words": 12
    }

    out = route(text, context=context)
    print("\n[ORCHESTRATION OUTPUT]")
    print(out)


if __name__ == "__main__":
    main()
