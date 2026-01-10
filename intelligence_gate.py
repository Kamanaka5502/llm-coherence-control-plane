# intelligence_gate.py
# Governance layer: observe → constrain → signal restraint
# No generation. No memory. No identity.

from collections import deque
import os

ENTROPY_MAX = float(os.getenv("ELYRIA_ENTROPY_MAX", 0.30))
WINDOW_SIZE = 10


class IntelligenceGate:
    def __init__(self):
        self.entropy_window = deque(maxlen=WINDOW_SIZE)
        self.active_constraints = set()
        self.identity_pressure = 0.0

    def extract_signal(self, text: str) -> str:
        return text.strip()

    def measure_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        unique_chars = len(set(text))
        return unique_chars / len(text)

    def process(self, text: str):
        signal = self.extract_signal(text)
        entropy = self.measure_entropy(signal)
        self.entropy_window.append(entropy)

        mean_entropy = (
            sum(self.entropy_window) / len(self.entropy_window)
            if self.entropy_window else 0.0
        )

        self.active_constraints.clear()
        if mean_entropy > ENTROPY_MAX:
            self.active_constraints.add("stabilize")

        snapshot = {
            "entropy": round(entropy, 4),
            "mean_entropy": round(mean_entropy, 4),
            "active_constraints": list(self.active_constraints),
            "identity_pressure": round(self.identity_pressure, 4),
        }

        dampening = 1.0
        if "stabilize" in self.active_constraints:
            dampening = 0.7

        return snapshot, dampening
