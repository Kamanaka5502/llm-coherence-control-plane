import json
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
BASE = Path(__file__).parent / "data"
before_path = BASE / "before.jsonl"
after_path = BASE / "after.jsonl"

def load_kt(path):
    t = []
    kt = []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            t.append(row["t"])
            kt.append(row["Kt"] if "Kt" in row else row["K_t"])
    return t, kt

# Load data
t_before, kt_before = load_kt(before_path)
t_after, kt_after = load_kt(after_path)

# Plot
plt.figure(figsize=(8, 5))
plt.plot(t_before, kt_before, marker="o", label="Before (Unchecked Recursion)")
plt.plot(t_after, kt_after, marker="o", label="After (ECP Enabled)")

plt.xlabel("Iteration (t)")
plt.ylabel("Coherence (Kₜ)")
plt.title("Coherence Over Recursive Interaction")
plt.legend()
plt.grid(True)

# Save
out = Path(__file__).parent / "kt_comparison.png"
plt.tight_layout()
plt.savefig(out, dpi=150)
plt.show()

print(f"Saved plot to {out}")
