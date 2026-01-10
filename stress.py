# stress.py
# Stress harness: applies controlled pressure via real CLI calls
# No interpretation. No feedback. No mutation.

import subprocess
import sys
import time

CASES = [
    ("short-calm", "hello"),
    ("medium-text", "hello elyria this is a normal sentence"),
    ("repetition", "hello " * 20),
    ("high-entropy", "".join(chr(33 + (i % 90)) for i in range(200))),
    ("long-repetition", "elyria " * 100),
]

CMD = [sys.executable, "-m", "elyria_cp.app", "new"]


def run_case(label, text):
    print(f"\n--- case: {label} ---")
    proc = subprocess.Popen(
        CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = proc.communicate(text + "\n", timeout=10)

    if out:
        print(out.strip())
    if err:
        print("stderr:", err.strip())


def main():
    print("ELYRIA STRESS HARNESS")
    print("=====================")

    for label, text in CASES:
        run_case(label, text)
        time.sleep(0.2)

    print("\nStress run complete.")


if __name__ == "__main__":
    main()

