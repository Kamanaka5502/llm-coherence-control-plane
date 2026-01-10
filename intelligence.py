# intelligence.py
# Bounded reasoning layer
# No memory. No authority. No side effects.

from execution_stub import execute
from execution_binding import may_execute
from dispatch import dispatch
from typing import Dict, Optional

from confidence import compute_confidence
from actuation_threshold import may_act
from capabilities import classify, extract_intent, summarize
from reflection import reflect
from intent_bindings import allowed_capabilities

def reason(text: str, context: Optional[Dict] = None) -> Dict[str, str]:
    """
    Perform bounded reasoning over explicit input.
    Context is accepted but not interpreted.
    """
    if context is None:
        context = {}

    text = text.strip()
    if not text:
        return {
            "status": "no-input",
            "analysis": "",
            "response": ""
        }

    analysis = (
        "Input received. Analyzing structure and intent "
        "without assuming context, identity, or history."
    )

    response = (
        "Statement acknowledged. No action taken "
        "without an explicit request."
    )

    return {
        "status": "ok",
        "analysis": analysis,
        "response": response,
    }


def route(text: str, context: Optional[Dict] = None) -> Dict[str, str]:
    """
    Read-only orchestration.
    Routes capabilities without authority.
    """
    if context is None:
        context = {}

    result = {
        "type": classify(text)["type"],
        "intent": extract_intent(text)["intent"],
    }

    if context.get("allow_summary"):
        result["summary"] = summarize(
            text,
            max_words=context.get("summary_words", 12)
        )["summary"]

    return result


def main():
    print("ELYRIA INTELLIGENCE (BASELINE)")
    print("------------------------------")

    text = input("reason → ").strip()

    # Explicit context only
    context = {
        "intent": "analyze_only"
    }

    result = reason(text, context=context)
    confidence = compute_confidence()

    annotated = {
        "result": result,
        "confidence": confidence
    }

    print("\n[ANNOTATED OUTPUT]")
    print(annotated)

    # Invariants snapshot (read-only)
    invariant_status = {
        "status": "CLEAN"
    }

    actuation_decision = may_act(
        confidence=confidence,
        invariant_status=invariant_status
    )

    print("\n[ACTUATION DECISION]")
    print(actuation_decision)

    # Orchestration (explicit, opt-in)
    orchestration = route(
        text,
        context={
            "allow_summary": True,
            "summary_words": 12
        }
    )

    print("\n[ORCHESTRATION]")
    print(orchestration)
    bindings = allowed_capabilities(
        intent=orchestration.get("intent"),
        confidence=confidence,
        invariant_status=invariant_status
    )

    print("\n[INTENT BINDINGS]")
    print(bindings)

    dispatch_result = dispatch(
        capabilities=bindings["allowed"],
        text=text
    )

    print("\n[DISPATCH]")
    print(dispatch_result)

    execution = may_execute(
        capabilities=bindings["allowed"],
        mode="dry-run",        # MUST stay dry-run unless explicitly changed
        operator_ok=False      # Explicit human opt-in required
    )

    print("\n[EXECUTION BINDING]")
    print(execution)

    if execution["decision"] == "ALLOW":
        result_exec = execute(
            capability=bindings["allowed"][0],
            text=text
        )

        print("\n[EXECUTION RESULT]")
        print(result_exec)
    else:
        print("\n[EXECUTION RESULT]")
        print({
            "status": "SKIPPED",
            "reason": execution["reason"]
        })


    reflection = reflect(
        text=text,
        reasoning=result,
        orchestration=orchestration,
        confidence=confidence
    )

    print("\n[REFLECTION]")
    print(reflection)


if __name__ == "__main__":
    main()
