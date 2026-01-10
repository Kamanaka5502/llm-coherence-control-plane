from collections import Counter

def analyze(nodes):
    if not nodes:
        return {}

    words = []
    for n in nodes:
        words.extend(n["text"].lower().split())

    counts = Counter(words)

    return {
        "total_nodes": len(nodes),
        "top_words": counts.most_common(5)
    }

def reflect(nodes):
    intel = analyze(nodes)
    if not intel:
        return "no signal yet"

    top = intel.get("top_words", [])
    if not top:
        return "signals are still forming"

    dominant, strength = top[0]

    if strength > 5:
        return f"focus is consolidating around '{dominant}'"
    elif strength > 2:
        return f"'{dominant}' is emerging as a theme"
    else:
        return "exploration phase — no dominant signal yet"
