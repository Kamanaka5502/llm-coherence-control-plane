# calibration.py
# External calibration runner (no core edits)

import subprocess
import sys
import re
import time
import os
from pathlib import Path

THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40]

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def run(cmd, env=None):
    p = subprocess.Popen(
        cmd,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate(timeout=30)
    if err.strip():
        print("stderr:", err.strip())
    return out


def parse_metrics(text):
    def grab(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else "NA"

    return {
        "observations": grab(r"observations\s*:\s*(\d+)"),
        "stabilization_rate": grab(r"stabilization rate\s*:\s*([\d\.%]+)"),
        "avg_entropy": grab(r"avg entropy\s*:\s*([\d\.]+)"),
        "avg_dampening": grab(r"avg dampening\s*:\s*([\d\.]+)"),
    }


def main():
    print("ELYRIA CALIBRATION")
    print("==================")
    print("threshold | obs | stab_rate | avg_entropy | avg_damp")
    print("----------+-----+-----------+-------------+----------")

    base_env = dict(os.environ)

    for t in THRESHOLDS:
        env = dict(base_env)
        env["ELYRIA_ENTROPY_MAX"] = str(t)

        # Run stress harness
        run([PY, "stress.py"], env=env)
        time.sleep(0.2)

        # Collect metrics
        metrics_out = run([PY, "metrics.py"], env=env)
        m = parse_metrics(metrics_out)

        print(
            f"{t:>9.2f} | "
            f"{m['observations']:>3} | "
            f"{m['stabilization_rate']:>9} | "
            f"{m['avg_entropy']:>11} | "
            f"{m['avg_dampening']:>8}"
        )


if __name__ == "__main__":
    main()
