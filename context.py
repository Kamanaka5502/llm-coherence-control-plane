context = {
    "source": "explicit",
    "timestamp": "runtime",
    "gate_snapshot": gate_snapshot,
    "policy": policy_snapshot,
    "invariants": invariants_snapshot,
    "intent": "analyze_only",
}
reason(text, context=context)
