# capture.py
# Explicit, opt-in snapshot capture
# Zero background authority
# Manual invocation only

from pathlib import Path
from datetime import datetime, timezone
import json

CAPTURE_LOG = Path.home() / ".elyria_capture.jsonl"


def capture(text: str):
    text = text.strip()
    if not text:
        print("empty capture ignored")
        return

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "text": text,
    }

    with CAPTURE_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    print("✓ snapshot captured")


def main():
    print("ELYRIA CAPTURE (OPT-IN)")
    print("----------------------")
    text = input("snapshot → ").strip()
    capture(text)


if __name__ == "__main__":
    main()
