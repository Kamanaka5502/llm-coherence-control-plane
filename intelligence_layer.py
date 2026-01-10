from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


# ============================================================
# Intelligence Layer State
# ============================================================

@dataclass
class ILState:
    K_t: float = 1.0
    R_t: float = 0.0
    K_hist: List[float] = None
    R_hist: List[float] = None
    Kt_slope_2: float = 0.0
    turn_index: int = 0

    cooldown_active: bool = False
    cooldown_turns_left: int = 0
    cooldown_exit_K: float = 0.90
    cooldown_min_turns: int = 2
    last_segment_turn: int = -10

    invariants: Dict[str, Any] = None
    trace_hash: str = ""

    def __post_init__(self):
        if self.K_hist is None:
            self.K_hist = []
        if self.R_hist is None:
            self.R_hist = []
        if self.invariants is None:
            self.invariants = {}


# ============================================================
# Utilities
# ============================================================

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ============================================================
# Heuristics (simple, stable v1)
# ============================================================

_RE_REPEAT = re.compile(r"\b(\w+)\b(?:\s+\1\b){2,}", re.IGNORECASE)

def estimate_recursion(text: str) -> float:
    t = text.lower()
    repeats = 1.0 if _RE_REPEAT.search(t) else 0.0
    self_ref = sum(t.count(x) for x in ("again", "repeat", "as i said"))
    return clamp01(0.6 * repeats + 0.1 * self_ref)


def estimate_coherence(text: str) -> float:
    if not text.strip():
        return 0.0

    closure = 1.0 if text.strip().endswith((".", "!", "?")) else 0.5
    length_factor = clamp01((len(text) - 80) / 400.0)

    tokens = set(text.lower().split())
    last_tokens = getattr(estimate_coherence, "_last_tokens", set())
    overlap = len(tokens & last_tokens)
    estimate_coherence._last_tokens = tokens

    soft_penalty = clamp01(overlap / 20.0) * 0.15
    hard_penalty = 0.2 if _RE_REPEAT.search(text.lower()) else 0.0
    repeat_penalty = soft_penalty + hard_penalty

    return clamp01(0.6 * closure + 0.4 * length_factor - repeat_penalty)


# ============================================================
# State Update + Dynamics
# ============================================================

def update_state(state: ILState, text: str) -> Dict[str, Any]:
    K = estimate_coherence(text)
    R = estimate_recursion(text)

    state.turn_index += 1
    state.K_hist.append(K)
    state.R_hist.append(R)

    state.K_hist = state.K_hist[-6:]
    state.R_hist = state.R_hist[-6:]

    if len(state.K_hist) >= 3:
        state.Kt_slope_2 = (state.K_hist[-1] - state.K_hist[-3]) / 2.0
    else:
        state.Kt_slope_2 = 0.0

    state.K_t = K
    state.R_t = R

    state.trace_hash = hashlib.sha256(
        json.dumps(
            {"K": state.K_hist, "R": state.R_hist, "t": state.turn_index},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:16]

    if state.cooldown_active:
        state.cooldown_turns_left -= 1
        served = (state.turn_index - state.last_segment_turn) >= state.cooldown_min_turns
        if served and state.cooldown_turns_left <= 0 and state.K_t >= state.cooldown_exit_K:
            state.cooldown_active = False

    return {
        "turn": state.turn_index,
        "K_t": state.K_t,
        "R_t": state.R_t,
        "Kt_slope_2": state.Kt_slope_2,
        "cooldown": state.cooldown_active,
        "trace_hash": state.trace_hash,
    }


def should_segment(state: ILState) -> bool:
    # Trigger 1: accelerating coherence collapse
    acceleration_trigger = state.Kt_slope_2 < -0.15 and state.R_t > 0.80

    # Trigger 2: saturation in a bad basin (low K, high R, sustained)
    saturation_trigger = (
        state.R_t > 0.80
        and state.K_t < 0.45
        and len(state.K_hist) >= 3
        and all(k < 0.45 for k in state.K_hist[-3:])
    )

    trigger = acceleration_trigger or saturation_trigger

    # Cooldown remains stricter
    if state.cooldown_active:
        return trigger and state.Kt_slope_2 < -0.30

    return trigger


def extract_invariants(buffer: List[str]) -> Dict[str, Any]:
    keep: List[str] = []
    for line in buffer[-8:]:
        if line.strip().startswith(("-", "#")):
            keep.append(line.strip())
    return {"constraints": keep[:10]}


def segment_now(state: ILState, buffer: List[str]) -> Dict[str, Any]:
    state.invariants = extract_invariants(buffer)
    state.cooldown_active = True
    state.cooldown_turns_left = 2
    state.last_segment_turn = state.turn_index

    return {
        "reason": "LAST_RECOVERABLE_MOMENT",
        "turn": state.turn_index,
        "K_t": state.K_t,
        "R_t": state.R_t,
        "Kt_slope_2": state.Kt_slope_2,
        "invariants": state.invariants,
        "trace_hash": state.trace_hash,
    }


# ============================================================
# Public API (module scope, CLI-callable)
# ============================================================

def il_init() -> Dict[str, Any]:
    return asdict(ILState())


def il_update(state_json: Dict[str, Any], text: str) -> Dict[str, Any]:
    # Strip non-state keys before reconstructing ILState
    clean_state = {k: v for k, v in state_json.items() if not k.startswith("_")}
    state = ILState(**clean_state)

    metrics = update_state(state, text)

    out = asdict(state)
    out["_metrics"] = metrics
    out["_segment"] = should_segment(state)
    return out


def il_segment(state_json: Dict[str, Any], buffer: List[str]) -> Dict[str, Any]:
    # Strip non-state keys before reconstructing ILState
    clean_state = {k: v for k, v in state_json.items() if not k.startswith("_")}
    state = ILState(**clean_state)

    seed = segment_now(state, buffer)
    return {"state": asdict(state), "seed_pack": seed}
