# actuation.py
# Dry-run actuation layer
# Converts policy recommendations into simulated actions
# NO side effects. NO enforcement.

from policy import analyze


def simulate_action(rec):
    if "lowering ENTROPY_MAX" in rec:
        return "SIMULATE: would decrease ENTROPY_MAX by 0.05"
    if "review input patterns" in rec:
        return "SIMULATE: would flag input sources for review"
    if "over-constrained" in rec:
        return "SIMULATE: would relax dampening slope slightly"
    if "operating within expected bounds" in rec:
        return "NO ACTION: system stable"
    return "UNKNOWN RECOMMENDATION"


def main():
    report = analyze()

    print("ELYRIA ACTUATION (DRY RUN)")
    print("=========================")

    recs = report.get("recommendations", [])
    if not recs:
        print("no recommendations")
        return

    for r in recs:
        action = simulate_action(r)
        print(f"- {action}")


if __name__ == "__main__":
    main()
